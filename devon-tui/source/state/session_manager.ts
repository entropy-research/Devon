// import axios from 'axios';
// import {
//     fromPromise,
//     setup,
//     assign,
//     fromTransition,
//     fromCallback,
//     EventObject,
//     sendTo,
//     enqueueActions
//     // createActor
// } from 'xstate';
// import { eventHandlingLogic, eventSourceActor } from './event_actor';


// type Message = {
//     text: string;
//     type: 'user' | 'agent' | 'command' | 'tool' | 'task' | 'thought' | 'error';
// };

// type ServerEventContext = {
//     messages: Message[];
//     ended: boolean;
//     modelLoading: boolean;
//     toolMessage: string;
//     userRequest: boolean;
//     gitData: {
//         base_commit: string | null;
//         commits: string[];
//     };
// }

// export const sessionMachine = setup({
//     types: {
//         events: {} as
//             | { type: 'serverEvent'; payload: any }
//             | { type: 'startStream' }
//             | { type: 'stopStream' },
//         context: {} as {
//             host: string;
//             retryCount: number;
//             name: string;
//             path: string;
//             reset: boolean;
//             serverEventContext: ServerEventContext;
//         },
//         input: {} as {
//             reset: boolean;
//             host: string;
//             name: string;
//             path: string;
//         },
//     },

//     actors: {
//         eventHandlingLogic,
//         eventSourceActor,
//         createSession: fromPromise(
//             async ({
//                 input,
//             }: {
//                 input: { host: string; name: string; path: string; reset: boolean };
//             }) => {
//                 console.log("starting server")
//                 // sleep for 5 sec
//                 await new Promise(resolve => setTimeout(resolve, 5000));

//                 if (input?.reset === true) {
//                     await axios.post(`${input?.host}/session/${input?.name}/reset`);
//                 }


//                 const encodedPath = encodeURIComponent(input?.path);
//                 const response = await axios.post(
//                     `${input?.host}/session?session=${input?.name}&path=${encodedPath}`,
//                 );
//                 return response;
//             },
//         ),
//         startSession: fromPromise(
//             async ({ input }: { input: { host: string; name: string } }) => {
//                 const response = await axios.post(
//                     `${input?.host}/session/${input?.name}/start`,
//                 );
//                 return response;
//             },
//         ),
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
//         loadEvents: fromPromise(
//             async ({
//                 input,
//             }: {
//                 input: { host: string; name: string };
//             }) => {
//                 const newEvents = (
//                     await axios.get(`${input?.host}/session/${input?.name}/events`)
//                 ).data;
//                 return newEvents
//             },
//         ),
//     },
// }).createMachine({
//     id: 'session',
//     initial: 'initial',
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
//                 actions: assign({
//                     serverEventContext: ({ event }) => {
//                         return event.snapshot.context
//                     }
//                 })
//             }
//         },
//     ],
//     context: ({ input }) => ({
//         host: input.host,
//         retryCount: 0,
//         name: input.name,
//         path: input.path,
//         reset: input.reset,
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


//     states: {
//         initial: {
//             invoke: {
//                 id: 'checkSession',
//                 src: 'checkSession',
//                 input: ({ context: { host, name } }) => ({ host, name }),
//                 onDone: {
//                     target: 'sessionExists',
//                 },
//                 onError: {
//                     target: 'sessionDoesNotExist',
//                 },
//             },
//         },
//         sessionDoesNotExist: {
//             invoke: {
//                 id: 'createSession',
//                 src: 'createSession',
//                 input: ({ context: { host, name, path, reset } }) => ({
//                     host,
//                     name,
//                     path,
//                     reset,
//                 }),
//                 onDone: {
//                     target: 'sessionExists',
//                     actions: sendTo('ServerEventSource', ({ self }) => {
//                         return {
//                             type: 'startStream',
//                             sender: self
//                         }
//                     }),
//                 },
//                 onError: {
//                     target: 'retryCreateSession',
//                 }
//             },
//         },
//         sessionExists: {
//             invoke: {
//                 id: 'loadEvents',
//                 src: 'loadEvents',
//                 input: ({ context: { host, name } }) => ({
//                     host,
//                     name,
//                 }),
//                 onDone: {
//                     target: 'sessionReady',
//                     actions: enqueueActions(({ enqueue, event }) => {
//                         for (let i = 0; i < event.output.length; i++) {
//                             enqueue.sendTo('ServerEventHandler', event.output[i]);
//                         }
//                     })
//                 },
//             },
//         },
//         sessionReady: {
//             invoke: {
//                 id: 'startSession',
//                 src: 'startSession',
//                 input: ({ context: { host, name } }) => ({ host, name }),
//                 onDone: {
//                     target: 'running',
//                 },
//                 onError: {
//                     target: 'retryStartSession',
//                 },
//             },
//         },
//         retryStartSession: {
//             after: {
//                 1000: 'sessionReady',
//             },
//         },
//         retryCreateSession: {
//             after: {
//                 1000: 'sessionDoesNotExist',
//             }
//         },
//         running: {
//             on: {
//                 serverEvent: {
//                     target: 'running',
//                     actions: sendTo('ServerEventHandler', ({ event }) => {
//                         return event.payload
//                     }),
//                     reenter: true,
//                 },
//             },
//             reenter: true,
//         },
//     },
// });
