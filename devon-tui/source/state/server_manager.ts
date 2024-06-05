import { setup, assign, fromPromise, ActorRefFrom, createActor } from 'xstate';

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
// const EventSource = require('eventsource');
import EventSource from 'eventsource';


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

// const createSessionActor = fromPromise(async ({
//         input,
//     }: {
//         input: { host: string; name: string; path: string; reset: boolean };
//     }) => {
//         console.log("starting server")
//         // sleep for 5 sec
//         await new Promise(resolve => setTimeout(resolve, 5000));

//         if (input?.reset === true) {
//             await axios.post(`${input?.host}/session/${input?.name}/reset`);
//         }


//         const encodedPath = encodeURIComponent(input?.path);
//         const response = await axios.post(
//             `${input?.host}/session?session=${input?.name}&path=${encodedPath}`,
//         );
//         return response;
//     }
// )

// const loadEventsActor = fromPromise(async ({
//         input,
//     }: {
//         input: { host: string; name: string };
//     }) => {
//         const newEvents = (
//             await axios.get(`${input?.host}/session/${input?.name}/events`)
//         ).data;
//         return newEvents
//     }
// )

// const startSessionActor = fromPromise(async ({
//         input,
//     }: {
//         input: { host: string; name: string };
//     }) => {
//         const response = await axios.post(`${input?.host}/session/${input?.name}/start`);
//         return response;
//     },
// )

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
        },
        input: {} as {
            reset: boolean;
            host: string;
            name: string;
            path: string;
        },
    },

    actors: {
        eventHandlingLogic,
        eventSourceActor,
        createSession: fromPromise(
            async ({
                input,
            }: {
                input: { host: string; name: string; path: string; reset: boolean };
            }) => {
                console.log("starting server")
                // sleep for 5 sec
                await new Promise(resolve => setTimeout(resolve, 5000));

                if (input?.reset === true) {
                    await axios.post(`${input?.host}/session/${input?.name}/reset`);
                }


                const encodedPath = encodeURIComponent(input?.path);
                const response = await axios.post(
                    `${input?.host}/session?session=${input?.name}&path=${encodedPath}`,
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
                        return response.data[i].name;
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
        }
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
                input: ({ context: { host, name, path, reset } }) => ({
                    host,
                    name,
                    path,
                    reset,
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


// const newSessionMachine = setup({
//     types: {
//         context: {} as {
//             reset: boolean;
//             host: string;
//             name: string;
//             path: string;
//             serverEventContext: ServerEventContext;
//         },
//     },
//     actors: {
//         createSession: createSessionActor,
//         loadEvents: loadEventsActor,
//         startSession: startSessionActor,
//         eventSourceActor: eventSourceActor,
//         eventHandlingLogic: eventHandlingLogic,
//         checkSession: fromPromise(
//             async ({ input }: { input: { host: string; name: string } }) => {
//                 const response = await axios.get(`${input?.host}/session`);

//                 for (let i = 0; i < response.data.length; i++) {
//                     if (response.data[i].name === input.name) {
//                         return response.data[i].name;
//                     }
//                 }
//                 throw new Error('Session not found');
//             },
//         ),
//         pauseSession: fromPromise(
//             async ({ input }: { input: { host: string; name: string } }) => {
//                 const response = await axios.post(`${input?.host}/session/${input?.name}/pause`);
//                 return response;
//             },
//         ),
//         resumeSession: fromPromise(
//             async ({ input }: { input: { host: string; name: string } }) => {
//                 const response = await axios.post(`${input?.host}/session/${input?.name}/resume`);
//                 return response;
//             },
//         ),
//         resetSession: fromPromise(
//             async ({ input }: { input: { host: string; name: string } }) => {
//                 // pause session first
//                 await axios.post(`${input?.host}/session/${input?.name}/pause`);
//                 const response = await axios.post(`${input?.host}/session/${input?.name}/reset`);
//                 return response;
//             },
//         ),
//     }
    
// }).createMachine({
//     context: ({ input } : { input: any }) => ({
//         reset: input.reset,
//         host: input.host,
//         name: input.name,
//         path: input.path,
//         serverEventContext: {
//             messages: [],
//             ended: false,
//             modelLoading: false,
//             toolMessage: '',
//             userRequest: false,
//             gitData: {
//                 base_commit: null,
//                 commits: [],
//             },
//         }
//     }),
//     invoke: [
//         {
//             id: 'ServerEventSource',
//             src: 'eventSourceActor',
//             input: ({ context: { host, name } }) => ({ host, name }),
//             onDone: {
//                 actions: ({ event }) => {
//                     console.log("event", event)
//                 }
//             }
//         },
//         {
//             id: 'ServerEventHandler',
//             src: 'eventHandlingLogic',
//             input: ({ context: { host, name } }) => ({ host, name }),
//             onSnapshot: {
//                 actions: [assign({
//                     serverEventContext: ({ event }) => {
//                         return event.snapshot.context
//                     }
//                 }),
//                 raise(({ event }) => {
//                     if (event.snapshot.context.ended) {
//                         return {
//                             type: 'session.ended'
//                         }
//                     } else {
//                         return {
//                             type: 'randomcrap'
//                         }
//                     }
//                 })
//             ]
//             }
//         },
//     ],
//     initial: 'creating',
//     states : {

//         error: {},
//         creating: {
            
//             initial: "initial",
//             states: {
//                 initial: {
//                     invoke: {
//                         id: 'checkSession',
//                         src: 'checkSession',
//                         input: ({ context: { host, name } }) => ({ host, name }),
//                         onDone: {
//                             target: 'sessionCreated',
//                         },
//                         onError: {
//                             target: 'sessionDoesNotExist',
//                         },
//                     },
//                 },
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
//                 sessionCreated: {
//                     type: 'final'
//                 }

//             },
//             onDone: {
//                 target: 'initializing'
//             }
//         },
//         initializing: {
//             invoke: {
//                 id: 'loadEvents',
//                 src: 'loadEvents',
//                 input: ({ context: { host, name } }) => ({
//                     host,
//                     name,
//                 }),
//             },
//             onDone: {
//                 target: 'starting'
//             }
//         },
//         reset:{
//             invoke: {
//                 id: 'resetSession',
//                 src: 'resetSession',
//                 input: ({ context: { host, name } }) => ({ host, name }),
//                 onDone: {
//                     target: 'initializing'
//                 }
//             },
//         },
//         starting: {
//             initial: "initial",
//             states: {
//                 initial: {
//                     invoke: {
//                         id: 'startSession',
//                         src: 'startSession',
//                         input: ({ context: { host, name } }) => ({ host, name }),
//                         onDone: {
//                             target: 'started',
//                         },
//                         onError: {
//                             target: 'retryStartSession',
//                         },
//                     },
//                 },
//                 retryStartSession: {
//                     after: {
//                         1000: 'starting',
//                     },
//                 },
//                 started: {
//                     type: 'final'
//                 }
                
//             },
//             onDone: {
//                 target: 'running'
//             }
//         },
//         running:{
//             invoke: {
//                 id: 'resumeSession',
//                 src: 'resumeSession',
//                 input: ({ context: { host, name } }) => ({ host, name }),
//             },
//             on: {
//                 "session.pause": {
//                     target: "paused"
//                 },
//                 "session.toggle": {
//                     target: "paused"
//                 },
//                 serverEvent: {
//                     target: 'running',
//                     actions: sendTo('ServerEventHandler', ({ event }) => {
//                         return event['payload']
//                     }),
//                     reenter: true,
//                 },
//             },
//         },
//         paused: {
//             invoke: {
//                 id: 'pauseSession',
//                 src: 'pauseSession',
//                 input: ({ context: { host, name } }) => ({ host, name }),
//             },
//             on: {
//                 "session.resume": {
//                     target: "running"
//                 },
//                 "session.toggle": {
//                     target: "running"
//                 }
//             },
//         },
//         stopped: {
//             type: "final"
//         }
//     }
// })

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

export class SessionManager {
    public sessions: Map<string, ActorRefFrom<typeof sessionMachine>> = new Map();

    constructor(private host: string) {}

    registerSession(sessionId: string, sessionName: string, path: string, reset: boolean) {
        this.sessions.set(sessionId, createActor(sessionMachine, { id: sessionId, input: { reset, host: this.host, name: sessionName, path } }));
    }

    startSession(sessionId: string) {
        this.sessions.get(sessionId)?.start();
    }

    stopSession(sessionId: string) {
        this.sessions.get(sessionId)?.stop();
    }

    getSession(sessionId: string) {
        return this.sessions.get(sessionId);
    }


}



// export const serverMachine = setup({
//     types: {
//         context: {} as {
//             host: string;
//             retryCount: number;
//             port: number;
//             refs: {
//                 [key: string]: ActorRefFrom<typeof newSessionMachine>;
//             };
//         },
//         input: {} as {
//             port: string | undefined;
//         } | {},
//         events: {} as
//         | { type: 'server.setup'}
//         | { type: 'server.shutdown'}
//         | { type: 'server.setupFailed'; payload: { port: number; }}
//         | { type: 'server.retry'; payload: { port: number; }}
//         | { type: 'server.spawnSession'; payload: { sessionId: string; apiKey: string; sessionName: string; path: string; reset: boolean }; }
//         | { type: 'session.setupFailed'; payload: { error: any; }},
//     },
//     actors: {
//         startServer: fromPromise(async ({input} : { input: any, system: any}) => {
//             // run  healthcheck
//             const response = await axios.get(`${input.host}/`);
//             return response.data;
//         }),
//         spawnSessionMachine: sessionMachine
//     },
// }).createMachine({
//     context: ({ input } : { input: any }) => ({
//         host: input.host,
//         retryCount: 0,
//         refs: {},
//         port: input.port // string or undefined, if undefined, we define it in setup
//     }),
//     id: 'serverMachine',
//     initial: 'setup',
//     states: {
//         setup: {
//             //use a promise actor here so that we can easily bail out
//             on:{
//                 "server.retry": {
//                     target: "setup",
//                     reenter: true
//                 },
//                 "server.setupFailed": {
//                     target: "shutdown"
//                 }
//             },
//             invoke: {
//                 id: 'startServer',
//                 src: 'startServer',
//                 input: ({ context }: {context: any, event: any}) => ({
//                     hello: context.retryCount,
//                     raise: true
//                 }),
//                 onDone: {
//                     target: 'running',
//                     actions: [
//                         assign({
//                             retryCount: () => (0)
//                         })
//                     ]
//                 },
//                 onError: {
//                     actions: [
//                         assign({
//                             retryCount: ({ context }) => (context.retryCount + 1)
//                         }),
//                         raise(({ context }) => { 
//                             console.log("retrying")
//                             if(context.retryCount > 5){
//                                 return {
//                                     type: 'server.setupFailed',
//                                     payload: {
//                                         port: context.port
//                                     }
//                                 }
//                             }
//                             return {
//                                 type: 'server.retry',
//                                 payload: {
//                                     port: context.port
//                                 }
//                             }
//                         })
//                     ]
//                 }
//             },
//         },
//         running: {
//             on: {
//                 'server.spawnSession': {
//                     actions: [
//                         ({ context }) => { console.log(context) }
//                     ],
//                     target: "spawnSessionMachine"
//                 },
//                 'server.shutdown': {
//                     target: 'shutdown'
//                 }
//             },
//             entry: [
//                 () => { console.log("entered running") }
//             ],
//         },
//         spawnSessionMachine: {
//             entry: [
//                 assign({
//                   refs: ({ context, spawn, event  }) => ({
//                     ...context.refs,
//                     [(event as any).payload?.sessionId]: spawn(sessionMachine, { 
//                     id: (event as any).payload?.sessionId,
//                     input: {
//                         reset: (event as any).payload?.reset,
//                         host: context.host,
//                         name: (event as any).payload?.sessionName,
//                         path: (event as any).payload?.path,
//                     }})})})],

//         },
//         shutdown: {
//             type: 'final',
//             entry: [
//                 () => console.log("shutdown entered"),
//                 ({ context }) => {
//                     for(const session of Object.values(context.refs)){
//                         session.send({ type: 'session.pause' })
//                         stopChild(session)
//                     };
//                 },
//                 assign({
//                     refs: undefined
//                 })
//             ],
//             exit: () => console.log("shutdown exited")
//         }
//     },
//     exit: () => { console.log("exited full machine") }
// })

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
