import { setup, assign, fromPromise, ActorRefFrom } from 'xstate';

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
    enqueueActions,
    raise
    // createActor
} from 'xstate';
// const EventSource = require('eventsource');
import EventSource from 'eventsource';


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

const createSessionActor = fromPromise(async ({
        input,
    }: {
        input: { host: string; name: string; path: string; agentConfig: any; };
    }) => {

        // sleep for 5 sec
        await new Promise(resolve => setTimeout(resolve, 5000));

        try {
            const response = await axios.post(`${input.host}/session`, input.agentConfig, {
                params: {
                    session: input?.name,
                    path: input?.path
                },
                headers: {
                    'Content-Type': 'application/json'
                }
            });
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
            console.log("RESET: ", input.reset
             )
            if (input?.reset === true) {
                console.log("resetting session")
                await axios.post(`${input?.host}/session/${input?.name}/reset`);
            }
    
            const newEvents = (
                await axios.get(`${input?.host}/session/${input?.name}/events`)
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

        const response = await axios.post(`${input?.host}/session/${input?.name}/start`);
        return response;
    },
)


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
        }
    },
    actors: {
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
                const response = await axios.post(`${input?.host}/session/${input?.name}/pause`);
                return response;
            },
        ),
        resumeSession: fromPromise(
            async ({ input }: { input: { host: string; name: string } }) => {
                const response = await axios.post(`${input?.host}/session/${input?.name}/resume`);
                return response;
            },
        ),
        resetSession: fromPromise(
            async ({ input }: { input: { host: string; name: string } }) => {
                // pause session first
                await axios.post(`${input?.host}/session/${input?.name}/pause`);
                const response = await axios.post(`${input?.host}/session/${input?.name}/reset`);
                return response;
            },
        ),
    }
}).createMachine({
    context: ({ input } : { input: any }) => ({
        reset: input.reset,
        host: input.host,
        name: input.name,
        path: input.path,
        agentConfig: undefined,
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
            id: EVENTHANDLER_ACTOR_ID,
            src: 'eventHandlingLogic',
            input: ({ context: { host, name } }) => ({ host, name }),
            onSnapshot: {
                actions: [
                    assign({
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
                        assign(({ context, event } : { context:any, event: any}) => ({ ...context, agentConfig: event.agentConfig }))
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
                    entry: sendTo(EVENTSOURCE_ACTOR_ID, ({ self }) => {
                        return {
                            type: 'startStream',
                            sender: self
                        }
                    }),
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

// const sessionMachine = setup({
//     types: {
//         context: {} as {
//             sessionId: string;
//             apiKey: string;
//             sessionName: string;
//             transitionActor: string | undefined;
//         },
//     },
//     actors: {
//         test: fromPromise(({ input }: { input: any}) => {
//             console.log(input)
//             if( input.cool === "randomId3"){
//                 console.log("Failed instantiation")
//                 throw Error("Instantiation failed")
//             }
//             return input
//         })
//     }
// }).createMachine({
//     context: ({ input } : { input: any}) => ({
//         sessionId: input.sessionId,
//         apiKey: input.apiKey,
//         sessionName: input.sessionName,
//         transitionActor: undefined
//     }),
//     initial: 'somestate',
//     states: {
//         somestate:{
//             invoke: {
//                 id: "test",
//                 src: "test",
//                 input: ({ context }: {context: any}) => ({ cool: context.sessionId }),
//                 onDone: {
//                     target: "terminate",
                    
//                     actions: [
//                         assign({
//                             transitionActor: ({context}) => (context.sessionName)
//                         })
//                     ]
//                 }
//             }
//         },
//         terminate: {
//             type: "final",
//             // entry: ({context}) => console.log(context),
//         }
//     },
//     entry: () => console.log("entering child machine"),
//     exit: () => console.log("exiting child machine"),
//     output: ({context}) => (context)
// })


//                 sessionDoesNotExist: {
//                     invoke: {
//                         id: 'createSession',
//                         src: 'createSession',
//                         input: ({ context: { host, name, path, reset } }) => ({
//                             host,
//                             name,
//                             path,
//                             reset,
//                         }),
//                         onDone: {
//                             target: 'sessionCreated',
//                             actions: sendTo('ServerEventSource', ({ self }) => {
//                                 return {
//                                     type: 'startStream',
//                                     sender: self
//                                 }
//                             }),
//                         },
//                         onError: {
//                             target: 'retryCreateSession',
//                         }
//                     },
//                 },
//                 retryCreateSession: {
//                     after: {
//                         1000: 'sessionDoesNotExist',
//                     }
//                 },


export const serverMachine = setup({
    types: {
        context: {} as {
            host: string;
            retryCount: number;
            refs: Map<string, ActorRefFrom<typeof newSessionMachine>>;
        },
        input: {} as {
            port: string | undefined;
        } | {},
        events: {} as
        | { type: 'server.setup'}
        | { type: 'server.rand'}
        | { type: 'server.shutdown'}
        | { type: 'server.setupFailed'}
        | { type: 'server.retry'}
        | { type: 'server.spawnSession'; payload: { sessionId: string; apiKey: string; sessionName: string; path: string; reset: boolean }; }
        | { type: 'session.setupFailed'; payload: { error: any; }},
    },
    actors: {
        startServer: fromPromise(async ({input} : { input: any, system: any}) => {
            // run  healthcheck
            const response = await axios.get(`${input.host}/`);
            return response.data;
        }),
        spawnSessionMachine: newSessionMachine
    },
}).createMachine({
    context: ({ input } : { input: any }) => ({
        host: input.host,
        retryCount: 0,
        refs: new  Map<string, ActorRefFrom<typeof newSessionMachine>>(),
    }),
    id: 'serverMachine',
    initial: 'setup',
    states: {
        setup: {
            //use a promise actor here so that we can easily bail out
            on:{
                "server.retry": {
                    target: "setup",
                    reenter: true
                },
                "server.setupFailed": {
                    target: "shutdown"
                }
            },
            invoke: {
                id: 'startServer',
                src: 'startServer',
                input: ({ context }: {context: any, event: any}) => ({
                    host: context.host, 
                    retryCount: context.retryCount,
                }),
                onDone: {
                    target: 'running',
                    actions: [
                        assign({
                            retryCount: () => (0)
                        })
                    ]
                },
                onError: {
                    target: 'retryServerStart',
                    actions: [
                        ({ event}) => { console.log(event.error)},
                        assign({
                            retryCount: ({ context }) => (context.retryCount + 1)
                        }),
                        raise(({ context, event }) => { 
                            console.log("retrying")
                            if(context.retryCount > 5){
                                return {
                                    type: 'server.setupFailed',
                                    payload: {
                                        error: event.error
                                    }
                                }
                            }
                            return {
                                type: 'server.rand',
                            }
                        })
                    ]
                }
            },
        },
        retryServerStart: {
            after: {
                1000: "setup"
            }
        },
        running: {
            on: {
                // 'server.spawnSession': {
                //     actions: [
                //         ({ context }) => { console.log(context) }
                //     ],
                //     target: "spawnSessionMachine"
                // },
                'server.shutdown': {
                    target: 'shutdown'
                }
            },
            entry: [
                () => { console.log("entered running") }
            ],
        },
        // spawnSessionMachine: {
        //     entry: [
        //         assign({
        //           refs: ({ context, spawn, event  }) => ({
        //             ...context.refs,
        //             [(event as any).payload?.sessionId]: spawn(sessionMachine, { 
        //             id: (event as any).payload?.sessionId,
        //             input: {
        //                 reset: (event as any).payload?.reset,
        //                 host: context.host,
        //                 name: (event as any).payload?.sessionName,
        //                 path: (event as any).payload?.path,
        //             }})})})],
        // },
        shutdown: {
            type: 'final',
            entry: [
                () => console.log("shutdown entered"),
                ({ context }) => {
                    for(const session of Object.values(context.refs)){
                        session.send({ type: 'session.pause' })
                        session.stop()
                    };
                },
                assign({
                    refs: undefined
                })
            ],
            exit: () => console.log("shutdown exited")
        }
    },
    exit: () => { console.log("exited full machine") }
})

// const serverActor = createActor(serverMachine, {
//   input: {},
// });

// serverActor.start()
// serverActor.send({ type: 'server.setup' })
// // let counter = 0
// // serverActor.subscribe((state : any) => {
// //     if (state.matches('running') && counter <= 3) {
// //         serverActor.send({ type: 'server.spawnSession', payload: { sessionId: `randomId${counter}`, apiKey: "randomKey", sessionName: "randomName", path: "randomPath"} });
// //         counter += 1
// //     } else if (state.matches('running')) {
// //         serverActor.send({ type: 'server.shutdown' })
// //     }
// // });

// serverActor.on("session.setupFailed", (event : any) => {
//     console.log(event)
// })
