import { setup, createActor, raise, assign, fromPromise, emit } from 'xstate';

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

const sessionMachine = setup({
    types: {
        context: {} as {
            sessionId: string;
            apiKey: string;
            sessionName: string;
            transitionActor: string | undefined;
        },
    },
    actors: {
        test: fromPromise(({ input }: { input: any}) => {
            console.log(input)
            if( input.cool === "randomId3"){
                console.log("Failed instantiation")
                throw Error("Instantiation failed")
            }
            return input
        })
    }
}).createMachine({
    context: ({ input } : { input: any}) => ({
        sessionId: input.sessionId,
        apiKey: input.apiKey,
        sessionName: input.sessionName,
        transitionActor: undefined
    }),
    initial: 'somestate',
    states: {
        somestate:{
            invoke: {
                id: "test",
                src: "test",
                input: ({ context }: {context: any}) => ({ cool: context.sessionId }),
                onDone: {
                    target: "terminate",
                    
                    actions: [
                        assign({
                            transitionActor: ({context}) => (context.sessionName)
                        })
                    ]
                }
            }
        },
        terminate: {
            type: "final",
            // entry: ({context}) => console.log(context),
        }
    },
    entry: () => console.log("entering child machine"),
    exit: () => console.log("exiting child machine"),
    output: ({context}) => (context)
})

const serverMachine =  setup({
    types: {
        context: {} as {
            host: string;
            retryCount: number;
            port: number;
            refs: any;
        },
        input: {} as {
            port: string | undefined;
        } | {},
        events: {} as
        | { type: 'server.setup';}
        | { type: 'server.shutdown';}
        | { type: 'server.setupFailed'; port: number; }
        | { type: 'server.retry'; port: number; }
        | { type: 'server.spawnSession'; payload: { sessionId: string; apiKey: string; sessionName: string }; }
        | { type: 'session.setupFailed'; error: any; },
    },
    actors: {
        startServer: fromPromise(async ({input} : { input: any, system: any}) => {
            console.log(input.hello)
            if(input.hello < 3){
                throw Error("1")
            }
            return input.hello
        }),
        spawnSessionMachine: sessionMachine
    },
}).createMachine({
    context: ({ input } : { input: any }) => ({
        host: input.host,
        retryCount: 0,
        refs: [],
        port: input.port // string or undefined, if undefined, we define it in setup
    }),
    id: 'serverMachine',
    initial: 'launch',
    states: {
        launch: {
            on: {
                "server.setup": {
                    target: "setup"
                }
            }
        },
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
                    hello: context.retryCount,
                    raise: true
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
                    actions: [
                        assign({
                            retryCount: ({ context }) => (context.retryCount + 1)
                        }),
                        raise(({ context }) => { 
                            console.log("retrying")
                            if(context.retryCount > 5){
                                return {
                                    type: 'server.setupFailed',
                                    port: context.port
                                }
                            }
                            return {
                                type: 'server.retry',
                                port: context.port
                            }
                        })
                    ]
                }
            },
        },
        running: {
            on: {
                'server.spawnSession': {
                    actions: [
                        ({ context }) => { console.log(context) }
                    ],
                    target: "spawnSessionMachine"
                },
                'server.shutdown': {
                    target: 'shutdown'
                }
            },
            entry: [
                () => { console.log("entered running") }
            ],
        },
        spawnSessionMachine: {
            invoke: {
                id: 'spawnSessionMachine',
                src: 'spawnSessionMachine',
                input: ({ event }: { event : { type: string, payload: any }}) => ({
                    sessionId: event.payload.sessionId,
                    apiKey: event.payload.sessionId,
                    sessionName: event.payload.sessionId
                }),
                onDone: {
                    target:"running",
                    actions: [
                        // ({event}) => console.log(event.output),
                        assign({
                            refs: ({ context, event }: { context: any, event: any}) => {
                                const thing = {...context.refs }
                                thing[event.output.sessionId] = event.output.transitionActor
                                return thing
                            }
                        })
                    ],
                },
                onError: {
                    target: "running",
                    actions: [
                        assign({
                            retryCount: ({ context }) => (context.retryCount + 1)
                        }),
                        emit(({event}) => ({
                            type: 'session.setupFailed',
                            error: event.error
                        }))
                    ],
                }
            }
        },
        shutdown: {
            type: 'final',
            entry: [
                () => console.log("shutdown entered"),
                ({ context }) => {
                    for(const sessionId in context.refs){
                        console.log(sessionId)
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

const serverActor = createActor(serverMachine, {
  input: {},
});

serverActor.start()
serverActor.send({ type: 'server.setup' })
let counter = 0
serverActor.subscribe(state => {
    if (state.matches('running') && counter <= 3) {
        serverActor.send({ type: 'server.spawnSession', payload: { sessionId: `randomId${counter}`, apiKey: "randomKey", sessionName: "randomName"} });
        counter += 1
    } else if (state.matches('running')) {
        serverActor.send({ type: 'server.shutdown' })
    }
});

serverActor.on("session.setupFailed", (event) => {
    console.log(event)
})
