import { setup, createActor, raise, assign, fromPromise, emit, stopChild, ActorRef, StateMachine, log } from 'xstate';

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
    | 'session.reset'
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
            case 'session.reset': {
                console.log("reset")
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
        if (event.type === 'reset') {
            eventStream?.removeEventListener('message', eventHandler);
            eventStream?.close();
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
            interval = setInterval(async () => {
                let new_state = await fetchSessionState(input.host, input.name)
                if (new_state !== state) {
                    state = new_state
                    sendBack({ type: 'session.stateUpdate', payload: state });
                }
            }, 100000);
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
    // await new Promise(resolve => setTimeout(resolve, 5000));

    try {
        console.log("path", input?.path,"config", input.agentConfig)
        const response = await axios.post(`${input.host}/sessions/${input?.name}`, input.agentConfig, {
            params: {
                // session: input?.name,
                path: input?.path
            },
            headers: {
                'Content-Type': 'application/json'
            }
        });
        console.log(response.request)
        return response;
    } catch (e) {
        console.log(e)
        throw e
    }
})

const loadEventsActor = fromPromise(async ({
    input,
}: {
    input: { host: string; name: string; reset: boolean };
}) => {
        try {
            const newEvents = (
                await axios.get(`${input?.host}/sessions/${input?.name}/events`)
            ).data;
            console.log("Loaded events: ", newEvents)
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

    const response = await axios.patch(`${input?.host}/sessions/${input?.name}/start`);
    
    const events = (await axios.get(`${input?.host}/sessions/${input?.name}/events`)).data;
    console.log("EVENTS IN START: ", events)

    const state = (await axios.get(`${input?.host}/sessions/${input?.name}/state`)).data;
    console.log("STATE IN START: ", state)

    return response;
})

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
        const response = await axios.post(`${host}/sessions/${name}/response`,{},{
            params: {
                response: message
            }
        });
    } else {
        const response = await axios.post(`${host}/sessions/${name}/event`, {
            type: 'Interrupt',
            content: message,
            producer: 'user',
            consumer: 'agent',
        });
    }
}

export const fetchSessionState = async (host: string, sessionId: string) => {
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
        checkServer: fromPromise(
            async ({ input }: { input: { host: string; } }) => {
                const response = await axios.get(`${input?.host}/`);
                return response;
            },
        ),
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
                const response = await axios.patch(`${input?.host}/sessions/${input?.name}/pause`);
                return response;
            },
        ),
        resetSession: fromPromise(
            async ({ input }: { input: { host: string; name: string } }) => {
                // pause session first

                console.log("RESETTING")
                await axios.patch(`${input?.host}/sessions/${input?.name}/pause`);
                const response = await axios.patch(`${input?.host}/sessions/${input?.name}/reset`);

                const state = (await axios.get(`${input?.host}/sessions/${input?.name}/state`)).data;
                console.log("STATE: ", state)

                return response;
            },
        ),
        deleteSession: fromPromise(
            async ({ input }: { input: { host: string; name: string } }) => {
                // pause session first
                const response = await axios.delete(`${input?.host}/sessions/${input?.name}`);
                return response;
            },
        )
    }
}).createMachine({
    context: ({ input }: { input: any }) => ({
        reset: input.reset,
        host: input.host,
        name: input.name,
        path: "",
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
            id: 'fetchSessionCallbackActor',
            src: 'fetchSessionCallbackActor',
            input: ({ context: { host, name } }) => ({ host, name }),
        },
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
    initial: 'setup',
    states: {
        setup: {
            initial: 'healthcheck',
            states: {
                healthcheck: {
                    initial: "check",
                    states: {
                        check: {
                            invoke: {
                                id: 'checkServer',
                                src: 'checkServer',
                                input: ({ context: { host } }) => ({ host }),
                                onDone: {
                                    target: 'done'
                                },
                                onError: {
                                    target: 'retry'
                                }
                            }
                        },
                        retry: {
                            after: {
                                5000: 'check'
                            }
                        },
                        done: {
                            type: 'final'
                        }
                    },
                    onDone: {
                        target: 'checkSession'
                    }
                },
                checkSession: {
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
                    }
                },
                sessionDoesNotExist: {
                    on: {
                        "session.create": {
                            target: "creating",
                            actions: [
                                () => console.log("start session"),
                                assign(({ context, event }) => ({ ...context, agentConfig: event.payload.agentConfig, path: event.payload.path }))
                            ]
                        }
                    }
                },
                creating: {
                    initial: "initial",
                    states: {
                        initial: {
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
                                    target: 'sessionCreated'
                                },
                                onError: {
                                    target: 'retryCreateSession',
                                }
                            },
                        },
                        retryCreateSession: {
                            after: {
                                1000: 'initial',
                            }
                        },
                        sessionCreated: {
                            type: 'final',
                        }

                    },
                    onDone: {
                        target: 'sessionExists'
                    }
                },
                sessionExists: {
                    type: "final"
                },
            },
            onDone: {
                target: "sessionReady"
            }
        },
        deleting : {
            invoke: {
                id: 'deleteSession',
                src: 'deleteSession',
                input: ({ context: { host, name } }) => ({ host, name }),
                onDone: {
                    target: 'setup'
                }
            }
        },
        sessionReady: {
            entry: [
                () => console.log("Session Ready!"), 
                emit(({ context }) => ({
                    type: "session.creationComplete",
                    name: context.name
                }))
            ],
            on: {
                "session.delete": {
                    target: "deleting",
                },
                "session.init": {
                    target: "initializing",
                }
            },
        },
        initializing: {
            entry: [() => console.log("initializing session"),
                sendTo(EVENTHANDLER_ACTOR_ID, ({ self }) => {
                    return {
                        type: 'session.reset',
                        sender: self
                    }
                })
            ],
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
            },
            exit: [
                sendTo(EVENTSOURCE_ACTOR_ID, ({ self }) => {
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
                })
            ]
        },
        resetting: {
            exit: [
                () =>  console.log("Successfully reset"),
                sendTo(EVENTHANDLER_ACTOR_ID, ({ self }) => {
                    return {
                        type: 'session.reset',
                        sender: self
                    }
                }),
            ],
            entry: () => console.log("resetting"),
            invoke: {
                id: "resetSession",
                src: "resetSession",
                input: ({ context: { host, name } }) => ({ host, name }),
                onDone: {
                    actions: [
                        sendTo(EVENTSOURCE_ACTOR_ID, ({ self }) => {
                            return {
                                type: 'stopStream',
                                sender: self
                            }
                        }),

                    ],
                    target: "initializing"
                },
            },

            // on: {
            //     "session.resume": {
            //         target: "starting"
            //     },
            //     "session.toggle": {
            //         target: "starting"
            //     },
            //     "session.reset": {
            //         target: "resetting"
            //     }
            // }
        },
        starting: {
            entry: () => console.log("Starting"),
            invoke: {
                id: 'startSession',
                src: 'startSession',
                input: ({ context: { host, name } }) => ({ host, name }),
                onDone: {
                    target: 'running'
                }
            },
            on: {
                "session.pause": {
                    target: "paused"
                },
                "session.reset": {
                    target: "resetting"
                },
                "session.toggle": {
                    target: "paused"
                }
            }
        },
        running: {
            on: {
                "session.pause": {
                    target: "paused"
                },
                "session.sendMessage": {
                    target: "running",
                    actions: [({ event, context }) => {
                        sendMessage({
                            host: context.host,
                            name: context.name,
                            message: event.message,
                            userResponse: context.serverEventContext.userRequest
                        })
                    },log("sending message")]
                },
                "session.toggle": {
                    target: "paused"
                },
                "session.reset": {
                    target: "resetting"
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
                    target: "starting"
                },
                "session.toggle": {
                    target: "starting"
                },
                "session.reset": {
                    target: "resetting"
                }
            },
        },
        stopped: {
            type: "final"
        },
        error: {}
    }
})