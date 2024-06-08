import { setup, createActor, raise, assign, fromPromise, emit, stopChild, ActorRef, StateMachine } from 'xstate';

// Server session machine

// Context object contains:
// 1. host
// 2. 

// root states:
// launch (created, started, but not running)
// setup server,
// server running,
// spawn session
// shutdown
import axios from 'axios';
import {
    fromTransition,
    fromCallback,
    EventObject,
    sendTo,
    enqueueActions
    // createActor
} from 'xstate';


type Message = {
    text: string;
    type: 'user' | 'agent' | 'command' | 'tool' | 'task' | 'thought' | 'error';
};

type ServerEvent = {
    type:
    | 'Init'
    | 'ModelResponse'
    | 'ToolResponse'
    | 'Task'
    | 'Interrupt'
    | 'UserRequest'
    | 'Stop'
    | 'ModelRequest'
    | 'ToolRequest'
    | 'Error'
    | 'UserResponse'
    | 'GitEvent';
    content: any;
    identifier: string | null;
};

type ServerEventContext = {
    messages: Message[];
    ended: boolean;
    modelLoading: boolean;
    toolMessage: string;
    userRequest: boolean;
    gitData: {
        base_commit: string | null;
        commits: string[];
    };
}

export const eventHandlingLogic = fromTransition(
    (
        state: ServerEventContext,
        event: ServerEvent,
    ) => {
        switch (event.type) {
            case 'Init': {
                return {
                    ...state,
                    messages: [],
                    ended: false,
                    modelLoading: false,
                    toolMessage: '',
                    userRequest: false,
                    gitData: {
                        base_commit: null,
                        commits: [],
                    },
                };
            }
            case 'Stop': {
                return { ...state, ended: true };
            }
            case 'ModelRequest': {
                return { ...state, modelLoading: true };
            }
            case 'ModelResponse': {
                let content = JSON.parse(event.content);
                return {
                    ...state,
                    modelLoading: false,
                    messages: [
                        ...state.messages,
                        { text: content.thought, type: 'thought' } as Message,
                    ],
                };
            }
            case 'ToolRequest': {
                return {
                    ...state,
                    toolMessage: 'Running command: ' + event.content.raw_command,
                };
            }
            case 'ToolResponse': {
                let tool_message = state.toolMessage + '\n> ' + event.content;
                if (tool_message.length > 2000) {
                    tool_message = tool_message.slice(2000);
                }

                return {
                    ...state,
                    toolMessage: '',
                    messages: [
                        ...state.messages,
                        { text: tool_message, type: 'tool' } as Message,
                    ],
                };
            }
            case 'Task': {
                return {
                    ...state,
                    messages: [
                        ...state.messages,
                        { text: event.content, type: 'task' } as Message,
                    ],
                };
            }
            case 'Interrupt': {
                return {
                    ...state,
                    messages: [
                        ...state.messages,
                        { text: event.content, type: 'user' } as Message,
                    ],
                };
            }
            case 'UserRequest': {
                return {
                    ...state,
                    userRequest: true,
                    messages: [
                        ...state.messages,
                        { text: event.content, type: 'agent' } as Message,
                    ],
                };
            }
            case 'UserResponse': {
                return {
                    ...state,
                    userRequest: false,
                    messages: [
                        ...state.messages,
                        { text: event.content, type: 'user' } as Message,
                    ],
                };
            }
            case 'Error': {
                console.error(event.content);
                return {
                    ...state,
                    messages: [
                        ...state.messages,
                        { text: event.content, type: 'error' } as Message,
                    ]
                };
            }
            case 'GitEvent': {
                if (event.content.type === 'base_commit') {
                    return {
                        ...state,
                        gitData: {
                            base_commit: event.content.commit,
                            commits: [event.content.commit],
                        },
                    };
                } else if (event.content.type === 'commit') {
                    return {
                        ...state,
                        gitData: {
                            base_commit: state.gitData.base_commit,
                            commits: [...state.gitData.commits, event.content.commit],
                        },
                    };
                } else if (event.content.type === 'revert') {
                    return {
                        ...state,
                        gitData: {
                            base_commit: event.content.commit,
                            commits: state.gitData.commits.slice(
                                0,
                                state.gitData.commits.indexOf(event.content.commit_to_go_to) +
                                1,
                            ),
                        },
                    };
                } else {
                    return state;
                }
            }

            default: {
                return state;
            }
        }
    },
    {
        messages: [],
        ended: false,
        modelLoading: false,
        toolMessage: '',
        userRequest: false,
        gitData: {
            base_commit: null,
            commits: [],
        },
    },
);

export const eventSourceActor = fromCallback<
    EventObject,
    { host: string; name: string }
>(({ input, receive, sendBack }) => {
    let eventStream: EventSource | null = null

    const eventHandler = ({ data }: { data: any }) => {
        sendBack({ type: 'serverEvent', payload: JSON.parse(data) });
    };

    receive((event: any) => {
        if (event.type === 'startStream') {
            eventStream = new EventSource(
                `${input.host}/sessions/${input.name}/events/stream`,
            );
            eventStream.addEventListener('message', eventHandler);
        }
        if (event.type === 'stopStream') {
            eventStream?.removeEventListener('message', eventHandler);
        }
    });

    return () => {
        eventStream?.removeEventListener('message', eventHandler);
        eventStream?.close();
    };
});

export const fetchSessionCallbackActor = fromCallback<
    EventObject,
    { host: string; name: string }
>(({ input, receive, sendBack }) => {

    let interval;
    let state;

    receive((event: any) => {
        if (event.type === 'startFetching') {
            interval = setInterval(async () => 
                {
                    let new_state = await fetchSessionState(input.host, input.name)
                    if (new_state !== state) {
                        state = new_state
                        sendBack({ type: 'session.stateUpdate', payload: state });
                    }
                }, 1000);
        }
        if (event.type === 'stopFetching') {
            clearInterval(interval);
        }
    })

    return () => {
        clearInterval(interval);
    };
});

const createSessionActor = fromPromise(async ({
        input,
    }: {
        input: { host: string; name: string; path: string; agentConfig: any; };
    }) => {

        // sleep for 5 sec
        await new Promise(resolve => setTimeout(resolve, 5000));

        try {
            const response = await axios.post(`${input.host}/sessions`, input.agentConfig, {
                params: {
                    session: input?.name,
                    path: input?.path
                },
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            console.log(response)
            return response;
        } catch (e) {
            console.log(e)
            throw e
        }
    }
)

const loadEventsActor = fromPromise(async ({
        input,
    }: {
        input: { host: string; name: string; reset: boolean};
    }) => {

        try {
            if (input?.reset === true) {
                console.log("resetting session")
                await axios.post(`${input?.host}/sessions/${input?.name}/reset`);
            }
    
            const newEvents = (
                await axios.get(`${input?.host}/sessions/${input?.name}/events`)
            ).data;

            return newEvents
        } catch (e) { 
            console.log(e)
        }
    }
)

const startSessionActor = fromPromise(async ({
        input,
    }: {
        input: { host: string; name: string; };
    }) => {

        const response = await axios.post(`${input?.host}/sessions/${input?.name}/start`);
        return response;
    },
)


const sendMessage = async ({
        host,
        name,
        message,
        userResponse
    }: {
        host: string;
        name: string;
        message: string;
        userResponse: boolean;
    }) => {
        if (userResponse) {
            const response = await axios.post(`${host}/sessions/${name}/response`, { message: message });
        } else {
            const response = await axios.post(`${host}/sessions/${name}/event`, {
                type: 'Interrupt',
                content: message,
                producer: 'user',
                consumer: 'agent',
            });
        }
}

export const fetchSessionState = async (host : string, sessionId : string) => {
    const { data } = await axios.get(
        `${host}/sessions/${encodeURIComponent(sessionId)}/state`
    )
    return data
}

const EVENTSOURCE_ACTOR_ID = 'ServerEventSource';
const EVENTHANDLER_ACTOR_ID = 'ServerEventHandler';


export const newSessionMachine = setup({
    types: {
        context: {} as {
            reset: boolean;
            host: string;
            name: string;
            path: string;
            serverEventContext: ServerEventContext;
            agentConfig: any;
            sessionState: any;
        },
    },
    actors: {
        fetchSessionCallbackActor: fetchSessionCallbackActor,
        createSession: createSessionActor,
        loadEvents: loadEventsActor,
        startSession: startSessionActor,
        eventSourceActor: eventSourceActor,
        eventHandlingLogic: eventHandlingLogic,
        checkSession: fromPromise(
            async ({ input }: { input: { host: string; name: string } }) => {
                const response = await axios.get(`${input?.host}/sessions`);

                for (let i = 0; i < response.data.length; i++) {
                    if (response.data[i].name === input.name) {
                        return response.data[i].name;
                    }
                }
                throw new Error('Session not found');
            },
        ),
        pauseSession: fromPromise(
            async ({ input }: { input: { host: string; name: string } }) => {
                console.log("PAUSING")
                const response = await axios.post(`${input?.host}/sessions/${input?.name}/pause`);
                return response;
            },
        ),
        resumeSession: fromPromise(
            async ({ input }: { input: { host: string; name: string } }) => {
                const response = await axios.post(`${input?.host}/sessions/${input?.name}/resume`);
                return response;
            },
        ),
        resetSession: fromPromise(
            async ({ input }: { input: { host: string; name: string } }) => {
                // pause session first
                await axios.post(`${input?.host}/sessions/${input?.name}/pause`);
                const response = await axios.post(`${input?.host}/sessions/${input?.name}/reset`);
                return response;
            },
        ),
        // sendMessage: sendMessageActor
    }
}).createMachine({
    context: ({ input } : { input: any }) => ({
        reset: input.reset,
        host: input.host,
        name: input.name,
        path: input.path,
        agentConfig: undefined,
        sessionState: undefined,
        serverEventContext: {
            messages: [],
            ended: false,
            modelLoading: false,
            toolMessage: '',
            userRequest: false,
            gitData: {
                base_commit: null,
                commits: [],
            },
        }
    }),
    invoke: [
        {
            id: EVENTSOURCE_ACTOR_ID,
            src: 'eventSourceActor',
            input: ({ context: { host, name } }) => ({ host, name }),
            onDone: {
                actions: ({ event }) => {
                    console.log("event", event)
                }
            }
        },
        {
            id: 'fetchSessionCallbackActor',
            src: 'fetchSessionCallbackActor',
            input: ({ context: { host, name } }) => ({ host, name }),
        },
        {
            id: EVENTHANDLER_ACTOR_ID,
            src: 'eventHandlingLogic',
            input: ({ context: { host, name } }) => ({ host, name }),
            onSnapshot: {
                actions: [assign({
                    serverEventContext: ({ event }) => {
                        return event.snapshot.context
                    }
                }),
                raise(({ event }) => {
                    if (event.snapshot.context.ended) {
                        return {
                            type: 'session.ended'
                        }
                    } else {
                        return {
                            type: 'randomcrap'
                        }
                    }
                })
            ]
            }
        },
    ],
    initial: 'idle',
    states : {
        error: {},
        idle: {
            on: {
                "session.begin": {
                    target: "creating",
                    actions: [
                        () => console.log("begin session"),
                        assign(({ context, event }) => ({ ...context, agentConfig: event.agentConfig }))
                    ]
                }
            }
        },
        creating: {
            initial: "initial",
            states: {
                initial: {
                    invoke: {
                        id: 'checkSession',
                        src: 'checkSession',
                        input: ({ context: { host, name } }) => ({ host, name }),
                        onDone: {
                            target: 'sessionExists',
                        },
                        onError: {
                            target: 'sessionDoesNotExist',
                        },
                    },
                },
                sessionDoesNotExist: {
                    invoke: {
                        id: 'createSession',
                        src: 'createSession',
                        input: ({ context: { host, name, path, agentConfig } }) => ({
                            host,
                            name,
                            path,
                            agentConfig
                        }),
                        onDone: {
                            target: 'sessionExists'
                        },
                        onError: {
                            target: 'retryCreateSession',
                        }
                    },
                },
                retryCreateSession: {
                    after: {
                        1000: 'sessionDoesNotExist',
                    }
                },
                sessionExists: {
                    type: 'final',
                    entry: [sendTo(EVENTSOURCE_ACTOR_ID, ({ self }) => {
                        return {
                            type: 'startStream',
                            sender: self
                        }
                    }),
                    sendTo('fetchSessionCallbackActor', ({ self }) => {
                        return {
                            type: 'startFetching',
                            sender: self
                        }
                    })]
                }

            },
            onDone: {
                target: 'initializing'
            }
        },
        //This is not good. Reset should be a conditional step here
        initializing: {
            entry: () => console.log("initializing session"),
            invoke: {
                id: 'loadEvents',
                src: 'loadEvents',
                input: ({ context: { host, name, reset } }) => ({
                    host,
                    name,
                    reset
                }),
                onDone: {
                    target: 'starting',
                    actions: enqueueActions(({ enqueue, event }) => {
                        for (let i = 0; i < event.output.length; i++) {
                            enqueue.sendTo(EVENTHANDLER_ACTOR_ID, event.output[i]);
                        }
                    })
                }
            }
        },
        reset:{
            invoke: {
                id: 'resetSession',
                src: 'resetSession',
                input: ({ context: { host, name } }) => ({ host, name }),
                onDone: {
                    target: 'paused',
                    // actions: [
                    //     sendTo(EVENTSOURCE_ACTOR_ID, ({ self }) => {
                    //         return {
                    //             type: 'RESET',
                    //             sender: self
                    //         }
                    //     })
                    // ]
                }
            },
        },
        starting: {
            entry: () => console.log("starting session"),
            initial: "initial",
            states: {
                initial: {
                    invoke: {
                        id: 'startSession',
                        src: 'startSession',
                        input: ({ context: { host, name } }) => ({ host, name }),
                        onDone: {
                            target: 'started',
                        },
                        onError: {
                            target: 'retryStartSession',
                        },
                    },
                },
                retryStartSession: {
                    after: {
                        1000: 'initial',
                    },
                },
                started: {
                    type: 'final'
                }
            },
            onDone: {
                target: 'running'
            }
        },
        resume: {
            invoke: {
                id: 'resumeSession',
                src: 'resumeSession',
                input: ({ context: { host, name } }) => ({ host, name }),
                onDone: {
                    target: 'running'
                }
            },
            on : {
                "session.pause": {
                    target: "paused"
                },
                "session.reset": {
                    target: "reset"
                },
                "session.toggle": {
                    target: "paused"
                }
            }
        },
        running:{
            on: {
                "session.pause": {
                    target: "paused"
                },
                "session.sendmessage": {
                    target: "running",
                    actions: ({ event, context}) => {
                        sendMessage({
                            host: context.host,
                            name: context.name,
                            message: event.message,
                            userResponse: context.serverEventContext.userRequest
                        })
                    }
                },
                "session.toggle": {
                    target: "paused"
                },
                "session.reset": {
                    target: "reset"
                },
                serverEvent: {
                    target: 'running',
                    actions: sendTo('ServerEventHandler', ({ event }) => {
                        console.log(event)
                        return event['payload']
                    }),
                    reenter: true,
                },
                "session.stateUpdate": {
                    target: "running",
                    actions: assign(({ event }) => {
                        return {
                            sessionState: event.payload
                        }
                    }),
                    reenter: true,
                }
            },
        },
        paused: {
            invoke: {
                id: 'pauseSession',
                src: 'pauseSession',
                input: ({ context: { host, name } }) => ({ host, name }),
            },
            on: {
                "session.resume": {
                    target: "resume"
                },
                "session.toggle": {
                    target: "resume"
                }
            },
        },
        stopped: {
            type: "final"
        }
    }
})