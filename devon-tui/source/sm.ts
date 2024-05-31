import axios from 'axios';
import {
    fromPromise,
    setup,
    assign,
    fromTransition,
    fromCallback,
    EventObject,
    sendTo,
    enqueueActions
    // createActor
} from 'xstate';
// const EventSource = require('eventsource');
import EventSource from 'eventsource';

// State Machine
// Requirements:
// Start the server
// Given a session name, either make a session or load it if it already exists
// Load all the events in the session and run the event handling logic on them
// Then start the above session
// start streaming the events from the server with http sse
// process the events and update the state accordingly
// Allow sending "events" to the server (and potentially support eager rendering of events)
//
// Invariants/properties
// - allow multiple sessions
// - allow CRUD of sessions
// - allow event handling logic to be ovverriden
// - state machine stuff should not support "persistence" directly, events should be loaded
// - allow branching (need to figure this out)




export type AgentConfig = {
    api_key: string;
    model: string;
    prompt_type: string | undefined;
    api_base: string | undefined;
}


type Message = {
    text: string;
    type: 'user' | 'agent' | 'command' | 'tool' | 'task' | 'thought' | 'error';
};

type ServerEvent = {
    type:
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
                `${input.host}/session/${input.name}/events/stream`,
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

export const sessionMachine = setup({
    types: {
        events: {} as
            | { type: 'serverEvent'; payload: any }
            | { type: 'startStream' }
            | { type: 'stopStream' },
        context: {} as {
            host: string;
            retryCount: number;
            name: string;
            path: string;
            reset: boolean;
            serverEventContext: ServerEventContext;
            agentConfig: AgentConfig;
        },
        input: {} as {
            reset: boolean;
            host: string;
            name: string;
            path: string;
            agentConfig: AgentConfig;
        },
    },

    actors: {
        eventHandlingLogic,
        eventSourceActor,
        createSession: fromPromise(
            async ({
                input,
            }: {
                input: { host: string; name: string; path: string; reset: boolean, agentConfig: AgentConfig };
            }) => {
                console.log("starting server")
                // sleep for 5 sec
                await new Promise(resolve => setTimeout(resolve, 5000));

                if (input?.reset === true) {
                    await axios.post(`${input?.host}/session/${input?.name}/reset`);
                }


                const encodedPath = encodeURIComponent(input?.path);
                console.log(
                    "config",
                    input.agentConfig
                )
                const response = await axios.post(
                    `${input?.host}/session?session=${input?.name}&path=${encodedPath}`,
                    {
                        ...input.agentConfig
                    }
                );
                return response;
            },
        ),
        startSession: fromPromise(
            async ({ input }: { input: { host: string; name: string } }) => {
                const response = await axios.post(
                    `${input?.host}/session/${input?.name}/start`,
                );
                return response;
            },
        ),
        checkSession: fromPromise(
            async ({ input }: { input: { host: string; name: string } }) => {
                const response = await axios.get(`${input?.host}/session`);

                for (let i = 0; i < response.data.length; i++) {
                    if (response.data[i].name === input.name) {
                        return response.data[i];
                    }
                }
                throw new Error('Session not found');
            },
        ),
        loadEvents: fromPromise(
            async ({
                input,
            }: {
                input: { host: string; name: string };
            }) => {
                const newEvents = (
                    await axios.get(`${input?.host}/session/${input?.name}/events`)
                ).data;
                return newEvents
            },
        ),
    },
}).createMachine({
    id: 'session',
    initial: 'initial',
    invoke: [
        {
            id: 'ServerEventSource',
            src: 'eventSourceActor',
            input: ({ context: { host, name } }) => ({ host, name }),
            onDone: {
                actions: ({ event }) => {
                    console.log("event", event)
                }
            }
        },
        {
            id: 'ServerEventHandler',
            src: 'eventHandlingLogic',
            input: ({ context: { host, name } }) => ({ host, name }),
            onSnapshot: {
                actions: assign({
                    serverEventContext: ({ event }) => {
                        return event.snapshot.context
                    }
                })
            }
        },
    ],
    context: ({ input }) => ({
        host: input.host,
        retryCount: 0,
        name: input.name,
        path: input.path,
        reset: input.reset,
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
        },
        agentConfig: input.agentConfig
    }),


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
                input: ({ context: { host, name, path, reset, agentConfig } }) => ({
                    host,
                    name,
                    path,
                    reset,
                    agentConfig
                }),
                onDone: {
                    target: 'sessionExists',
                    actions: sendTo('ServerEventSource', ({ self }) => {
                        return {
                            type: 'startStream',
                            sender: self
                        }
                    }),
                },
                onError: {
                    target: 'retryCreateSession',
                }
            },
        },
        sessionExists: {
            invoke: {
                id: 'loadEvents',
                src: 'loadEvents',
                input: ({ context: { host, name } }) => ({
                    host,
                    name,
                }),
                onDone: {
                    target: 'sessionReady',
                    actions: enqueueActions(({ enqueue, event }) => {
                        for (let i = 0; i < event.output.length; i++) {
                            enqueue.sendTo('ServerEventHandler', event.output[i]);
                        }
                    })
                },
            },
        },
        sessionReady: {
            invoke: {
                id: 'startSession',
                src: 'startSession',
                input: ({ context: { host, name } }) => ({ host, name }),
                onDone: {
                    target: 'running',
                },
                onError: {
                    target: 'retryStartSession',
                },
            },
        },
        retryStartSession: {
            after: {
                1000: 'sessionReady',
            },
        },
        retryCreateSession: {
            after: {
                1000: 'sessionDoesNotExist',
            }
        },
        running: {
            on: {
                serverEvent: {
                    target: 'running',
                    actions: sendTo('ServerEventHandler', ({ event }) => {
                        return event.payload
                    }),
                    reenter: true,
                },
            },
            reenter: true,
        },
    },
});
