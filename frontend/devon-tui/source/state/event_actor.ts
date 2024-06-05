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
// // const EventSource = require('eventsource');
// import EventSource from 'eventsource';

// // State Machine
// // Requirements:
// // Start the server
// // Given a session name, either make a session or load it if it already exists
// // Load all the events in the session and run the event handling logic on them
// // Then start the above session
// // start streaming the events from the server with http sse
// // process the events and update the state accordingly
// // Allow sending "events" to the server (and potentially support eager rendering of events)
// //
// // Invariants/properties
// // - allow multiple sessions
// // - allow CRUD of sessions
// // - allow event handling logic to be ovverriden
// // - state machine stuff should not support "persistence" directly, events should be loaded
// // - allow branching (need to figure this out)

// // Session Machine States
// // - initial
// // - createOrLoadSession
// // - create session
// // - retryCreateSession
// // - sessionCreated
// // - loadSession
// // - sessionReady
// // - loadEvents
// // - startEventListener
// // - startSession
// // - retryStartSession
// // - SessionRunning
// // - SessionEnded
// // - SendEventSession


// type Message = {
//     text: string;
//     type: 'user' | 'agent' | 'command' | 'tool' | 'task' | 'thought' | 'error';
// };

// type ServerEvent = {
//     type:
//     | 'ModelResponse'
//     | 'ToolResponse'
//     | 'Task'
//     | 'Interrupt'
//     | 'UserRequest'
//     | 'Stop'
//     | 'ModelRequest'
//     | 'ToolRequest'
//     | 'Error'
//     | 'UserResponse'
//     | 'GitEvent';
//     content: any;
//     identifier: string | null;
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

// export const eventHandlingLogic = fromTransition(
//     (
//         state: ServerEventContext,
//         event: ServerEvent,
//     ) => {
//         switch (event.type) {
//             case 'Stop': {
//                 return { ...state, ended: true };
//             }
//             case 'ModelRequest': {
//                 return { ...state, modelLoading: true };
//             }
//             case 'ModelResponse': {
//                 let content = JSON.parse(event.content);
//                 return {
//                     ...state,
//                     modelLoading: false,
//                     messages: [
//                         ...state.messages,
//                         { text: content.thought, type: 'thought' } as Message,
//                     ],
//                 };
//             }
//             case 'ToolRequest': {
//                 return {
//                     ...state,
//                     toolMessage: 'Running command: ' + event.content.raw_command,
//                 };
//             }
//             case 'ToolResponse': {
//                 let tool_message = state.toolMessage + '\n> ' + event.content;
//                 if (tool_message.length > 2000) {
//                     tool_message = tool_message.slice(2000);
//                 }

//                 return {
//                     ...state,
//                     toolMessage: '',
//                     messages: [
//                         ...state.messages,
//                         { text: tool_message, type: 'tool' } as Message,
//                     ],
//                 };
//             }
//             case 'Task': {
//                 return {
//                     ...state,
//                     messages: [
//                         ...state.messages,
//                         { text: event.content, type: 'task' } as Message,
//                     ],
//                 };
//             }
//             case 'Interrupt': {
//                 return {
//                     ...state,
//                     messages: [
//                         ...state.messages,
//                         { text: event.content, type: 'user' } as Message,
//                     ],
//                 };
//             }
//             case 'UserRequest': {
//                 return {
//                     ...state,
//                     userRequest: true,
//                     messages: [
//                         ...state.messages,
//                         { text: event.content, type: 'agent' } as Message,
//                     ],
//                 };
//             }
//             case 'UserResponse': {
//                 return {
//                     ...state,
//                     userRequest: false,
//                     messages: [
//                         ...state.messages,
//                         { text: event.content, type: 'user' } as Message,
//                     ],
//                 };
//             }
//             case 'Error': {
//                 console.error(event.content);
//                 return {
//                     ...state,
//                     messages: [
//                         ...state.messages,
//                         { text: event.content, type: 'error' } as Message,
//                     ]
//                 };
//             }
//             case 'GitEvent': {
//                 if (event.content.type === 'base_commit') {
//                     return {
//                         ...state,
//                         gitData: {
//                             base_commit: event.content.commit,
//                             commits: [event.content.commit],
//                         },
//                     };
//                 } else if (event.content.type === 'commit') {
//                     return {
//                         ...state,
//                         gitData: {
//                             base_commit: state.gitData.base_commit,
//                             commits: [...state.gitData.commits, event.content.commit],
//                         },
//                     };
//                 } else if (event.content.type === 'revert') {
//                     return {
//                         ...state,
//                         gitData: {
//                             base_commit: event.content.commit,
//                             commits: state.gitData.commits.slice(
//                                 0,
//                                 state.gitData.commits.indexOf(event.content.commit_to_go_to) +
//                                 1,
//                             ),
//                         },
//                     };
//                 } else {
//                     return state;
//                 }
//             }

//             default: {
//                 return state;
//             }
//         }
//     },
//     {
//         messages: [],
//         ended: false,
//         modelLoading: false,
//         toolMessage: '',
//         userRequest: false,
//         gitData: {
//             base_commit: null,
//             commits: [],
//         },
//     },
// );

// export const eventSourceActor = fromCallback<
//     EventObject,
//     { host: string; name: string }
// >(({ input, receive, sendBack }) => {
//     let eventStream: EventSource | null = null

//     const eventHandler = ({ data }: { data: any }) => {
//         sendBack({ type: 'serverEvent', payload: JSON.parse(data) });
//     };

//     receive((event: any) => {
//         if (event.type === 'startStream') {
//             eventStream = new EventSource(
//                 `${input.host}/session/${input.name}/events/stream`,
//             );
//             eventStream.addEventListener('message', eventHandler);
//         }
//         if (event.type === 'stopStream') {
//             eventStream?.removeEventListener('message', eventHandler);
//         }
//     });

//     return () => {
//         eventStream?.removeEventListener('message', eventHandler);
//         eventStream?.close();
//     };
// });
