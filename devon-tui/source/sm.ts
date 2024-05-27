import axios from 'axios';
import { fromPromise, setup, assign, fromTransition } from 'xstate';


export const sessionMachine = setup({
    types: {
        context: {} as {
            port: number;
            retryCount: number;
            name: string;
            path: string;
            reset: boolean;
        },
        input: {} as {
            reset: boolean;
            port: number;
            name: string;
            path: string;
        },
    },

    actors: {
        createSession: fromPromise(async ({ input }: { input: { port: number, name: string, path: string, reset: boolean } }) => {
            if(input?.reset === true){
                await axios.post(
                    `http://localhost:${input?.port}/session/${input?.name}/reset`,
                );
            }

            const encodedPath = encodeURIComponent(input?.path);
            const response = await axios.post(
                `http://localhost:${input?.port}/session?session=${input?.name}&path=${encodedPath}`,
            );
            return response;
        }),
        startSession: fromPromise(async ({ input }: { input: { port: number, name: string } }) => {
            const response = await axios.post(
                `http://localhost:${input?.port}/session/${input?.name}/start`,
            );
            return response;
        }),
    },
}).createMachine({
    id: 'session',
    initial: 'initial',
    context: ({input}) => ({
        port: input.port,
        retryCount: 0,
        name: input.name,
        path: input.path,
        reset: input.reset
    }),
    states: {
        initial: {
            invoke: {
                id: 'createSession',
                src: 'createSession',
                input: ({ context: { port, name, path, reset } }) => ({ port, name, path, reset }),
                onDone: {
                    target: 'sessionCreated',
                },
                onError: {
                    target: 'retryCreateSession',
                    actions: assign({
                        retryCount: (event) => event.context.retryCount + 1
                    }),
                },

            },
        },
        retryCreateSession: {
            after: {
                1000: 'initial'
            }
        },
        sessionCreated: {
            invoke: {
                id: 'startSession',
                src: 'startSession',
                input: ({ context: { port, name } }) => ({ port, name }),
                onDone: {
                    target: 'running',
                },
                onError: {
                    target: 'retryStartSession',
                },
            }
        },
        retryStartSession: {
            after: {
                1000: 'sessionCreated'
            }
        },
        running :{
            on: {
                SESSION_ENDED: 'initial',
            }
        }
    },
});

type Message = {
	text: string;
	type: 'user' | 'agent' | 'command' | 'tool' | 'task' | 'thought' | 'error';
};


type Event = {
	type:
		| 'ModelResponse'
		| 'ToolResponse'
		| 'Task'
		| 'Interrupt'
		| 'UserRequest'
		| 'Stop'
		// | 'EnvironmentRequest'
		// | 'EnvironmentResponse'
		| 'ModelRequest'
		| 'ToolRequest'
		| 'Error'
		| 'UserResponse';
	content: any;
	identifier: string | null;
};

export const eventHandlingLogic = fromTransition((state : {
    messages : Message[];
    ended : boolean;
    modelLoading : boolean;
    toolMessage : string;
    userRequest : boolean;
}, event : Event) => {
    switch (event.type) {
        case 'Stop': {
            return {...state, ended: true };
        }
        case 'ModelRequest': {
            return {...state, modelLoading: true };
        }
        case 'ModelResponse': {
            let content = JSON.parse(event.content);
            return {...state, modelLoading: false, messages: [...state.messages, { text: content.thought, type: 'thought' } as Message] };
        }
        case 'ToolRequest': {
            return {...state, toolMessage: 'Running command: ' + event.content.raw_command};
        }
        case 'ToolResponse': {
            let tool_message = state.toolMessage + '\n> ' + event.content;
			if (tool_message.length > 2000) {
				tool_message = tool_message.slice(2000);
			}

            return {...state, toolMessage: "", messages: [...state.messages, { text: tool_message, type: 'tool' } as Message] };
        }
        case 'Task': {
            return {...state, messages: [...state.messages, { text: event.content, type: 'task' } as Message] };
        }
        case 'Interrupt': {
            return {...state, messages: [...state.messages, { text: event.content, type: 'user' } as Message] };
        }
        case 'UserRequest': {
            return {...state, userRequest: true, messages: [...state.messages, { text: event.content, type: 'agent' } as Message] };
        }
        case 'UserResponse': {
            return {...state, userRequest: false, messages: [...state.messages, { text: event.content, type: 'user' } as Message] };
        }
        case 'Error': {
            console.error(event.content);
            return {...state, messages: [...state.messages, { text: event.content, type: 'error' } as Message] };
        }
        default: {
            return state;
        }
    }
}, { messages: [], ended: false, modelLoading: false, toolMessage: "", userRequest: false}); // Initial state

// type Message = {
// 	text: string;
// 	type: 'user' | 'agent' | 'command' | 'tool' | 'task' | 'thought' | 'error';
// };


// let eventMachine = setup({
//     types: {
//         context: {} as {
//             messages : Message[];
//             toolMessage : string;
            
//         },
//         events: {} as {
//             type: 'ModelRequest' | 'ModelResponse' | 'ToolRequest' | 'ToolResponse' | 'UserRequest' | 'UserResponse' | 'Interrupt' | 'Error' | 'Stop';
//             content: string;
//         }

//     },
// }).createMachine({
//     context: {
//         messages : [],
//         toolMessage : ""
//     },
//     initial: 'initial',
//     states: {
//         initial : {
//             on: {
//                 'ModelRequest': {
//                     target: 'model',
//                 },
//                 'ToolRequest' : {
//                     target : 'tool',
//                     actions: assign({
//                         toolMessage: ({event}) => event.content
//                     })
//                 },
//                 'Interrupt': {
//                     actions: assign({
//                         messages: ({context, event}) => [...context.messages, { text: event.content, type: 'user' }]
//                     })
//                 },
//                 'UserRequest': {
//                     target: 'userRequest',
//                     actions: assign({
//                         messages: ({context, event}) => [...context.messages, { text: event.content, type: 'agent' }]
//                     })
//                 },

//                 'Error': {
//                     actions: assign({
//                         messages: ({context, event}) => [...context.messages, { text: event.content, type: 'error' }]
//                     })
//                 },
//                 'Stop': {
//                     target: 'stop',
//                 }
//             }
//         },
//         model : {
//             on: {
//                 'ModelResponse': {
//                     target: 'initial',
//                     actions: assign({
//                         messages: ({context, event}) => [...context.messages, { text: event.content, type: 'agent' }]
//                     })
//                 }
//             }
//         },
//         tool : {
//             on: {
//                 'ToolResponse': {
//                     target: 'initial',
//                     actions: assign({
//                         messages: ({context, event}) => [...context.messages, { text: event.content, type: 'agent' }]
//                     })
//                 }
//             }
//         },
//         userRequest: {
//             on: {
//                 'UserResponse': {
//                     target: 'initial',
//                     actions:assign({
//                         messages: ({context, event}) => [...context.messages, { text: event.content, type: 'user' }]
//                     })
//                 }
//             }
//         },
//         stop : {
//             type: 'final'
//         }
//     }
// });


// const sessionActor = createActor(sessionMachine, {
//     input: {
//         port: 10000,
//         name: 'cli',
//         path: '/'
//     },
// });

