import React, {useState} from 'react';
import {Box, Text, useInput, useApp, Static} from 'ink';
import TextInput from 'ink-text-input';
import axios from 'axios';
import Spinner from 'ink-spinner';
import {useMachine, useActor} from '@xstate/react';
import { sessionMachine, eventHandlingLogic } from './sm.js';
// import {writeLogLine} from './utils.js';

// const createSession = async (port: number, path: string) => {
// 	let success = false;
// 	while (!success) {
// 		try {
// 			const encodedPath = encodeURIComponent(path);
// 			const response = await axios.post(
// 				`http://localhost:${port}/session?session=cli&path=${encodedPath}`,
// 			);
// 			return response;
// 		} catch (error: any) {
// 			await new Promise(resolve => setTimeout(resolve, 1000)); // Wait for 1 second before retrying
// 		}
// 	}
// 	return false;
// };

// const startSession = async (
// 	port: number,
// 	setStarted: (value: boolean) => void,
// ) => {
// 	let success = false;
// 	while (!success) {
// 		try {
// 			const response = await axios.post(
// 				`http://localhost:${port}/session/cli/start`,
// 			);
// 			setStarted(true);
// 			return response.data;
// 		} catch (error: any) {
// 			await new Promise(resolve => setTimeout(resolve, 1000)); // Wait for 1 second before retrying
// 		}
// 	}
// };

const fetchEvents = async (port: number) => {
	try {
		const response = await axios.get(
			`http://localhost:${port}/session/cli/events`,
		);
		return response.data;
	} catch (error: any) {
		// console.error('Error:', error.message);
	}
};

const giveUserReponse = async (port: number, res: string) => {
	try {
		const response = await axios.post(
			`http://localhost:${port}/session/cli/response?response=` + res,
		);
		return response.data;
	} catch (error: any) {
		// console.error('Error:', error.message);
	}
};

const sendInterrupt = async (port: number, res: string) => {
	try {
		// writeLogLine('interrupt: ' + res);
		const response = await axios.post(
			`http://localhost:${port}/session/cli/interrupt?message=` + res,
		);
		return response.data;
	} catch (error: any) {
		// console.error('Error:', error.message);
	}
};

// type Event = {
// 	type:
// 		| 'ModelResponse'
// 		| 'ToolResponse'
// 		| 'Task'
// 		| 'Interrupt'
// 		| 'UserRequest'
// 		| 'Stop'
// 		// | 'EnvironmentRequest'
// 		// | 'EnvironmentResponse'
// 		| 'ModelRequest'
// 		| 'ToolRequest'
// 		| 'Error'
// 		| 'UserResponse';
// 	content: any;
// 	identifier: string | null;
// };

// type Message = {
// 	text: string;
// 	type: 'user' | 'agent' | 'command' | 'tool' | 'task' | 'thought' | 'error';
// };

// const handleEvents = (
// 	events: Event[],
// 	setUserRequested: (value: boolean) => void,
// 	setModelLoading: (value: boolean) => void,
// 	exit: () => void,
// ) => {
// 	const messages: Message[] = [];
// 	let user_request = false;
// 	let model_loading = false;
// 	let tool_message = '';
// 	let idx = 0;
// 	let error = false;

// 	for (const event of events) {
// 		if (event.type == 'Stop') {
// 			console.log('Devon has left the chat.');
// 			exit();
// 		}

// 		if (event.type == 'ModelRequest') {
// 			model_loading = true;
// 		}

// 		if (event.type == 'ModelResponse') {
// 			let content = JSON.parse(event.content);
// 			model_loading = false;
// 			messages.push({text: content.thought, type: 'thought'});
// 		}

// 		if (event.type == 'ToolRequest') {
// 			tool_message = 'Running command: ' + event.content.raw_command;
// 		}

// 		if (event.type == 'ToolResponse') {
// 			tool_message += '\n> ' + event.content;
// 			if (tool_message.length > 2000) {
// 				messages.push({text: tool_message.slice(0, 2000), type: 'tool'});
// 			} else {
// 				messages.push({text: tool_message, type: 'tool'});
// 			}
// 			tool_message = '';
// 		}

// 		if (event.type == 'Task') {
// 			messages.push({text: event.content, type: 'task'});
// 		}

// 		if (event.type == 'Interrupt') {
// 			// writeLogLine('interrupt: ' + event.content);
// 			messages.push({text: event.content, type: 'user'});
// 		}

// 		if (event.type == 'UserResponse') {
// 			messages.push({text: event.content, type: 'user'});
// 			user_request = false;
// 		}

// 		if (event.type == 'UserRequest') {
// 			messages.push({text: event.content, type: 'agent'});
// 			user_request = true;
// 		}

// 		if (event.type == 'Error') {
// 			if (!error) {
// 				console.error('Error:', event.content);
// 				messages.push({text: event.content, type: 'error'});
// 				error = true;
// 			}
// 		}


// 		idx += 1;
// 	}
// 	setUserRequested(user_request);
// 	setModelLoading(model_loading);
// 	return messages;
// };

export const App = ({port, reset}: {port: number, reset: boolean}) => {
	const [inputValue, setInputValue] = useState('');
	// const [userRequested, setUserRequested] = useState(false);
	const [eventState,sendEvent] = useActor(eventHandlingLogic)
	// const [started, setStarted] = useState(false);
	const [state] = useMachine(sessionMachine,{
		input: {
			port: port,
			name: 'cli',
			path: process.cwd(),
			reset: reset
		}
	})
	let status = '';

	const {exit} = useApp();
	let eventI = 0;

	if (!state.matches('running')) {
		status = 'Initializing...';
	} else if (eventState.context.modelLoading) {
		status = 'Waiting for Devon...';
	} else if (eventState.context.userRequest) {
		status = 'Type your message:';
	} else {
		status = 'Interrupt:';
	}

	React.useEffect(() => {
		const interval = setInterval(async () => {
			if(state.matches('running')){
				const newEvents = await fetchEvents(port);
				if (newEvents) {
					for (let i = eventI; i < newEvents.length; i++) {
						sendEvent(newEvents[i]);
						eventI++;
					}
				}
			}
		}, 1000);

		return () => clearInterval(interval);
	}, [state]);

	useInput((_: any, key: any) => {
		if (key.escape) {
			exit();
		}
	});

	const handleSubmit = () => {
		if (state.matches('running') && inputValue.trim() !== '') {
			setInputValue('');
			if (inputValue.toLowerCase() == 'exit') {
				exit();
			}

			if (eventState.context.userRequest) {
				giveUserReponse(port, inputValue);
			} else {
				sendInterrupt(port, inputValue);
			}
		}
	};
	let messages = eventState.context.messages;

	return (
		<Box
			flexDirection="column"
			height="100%"
			borderStyle="classic"
			borderColor="white"
		>
			<Box flexDirection="column" paddingY={1}>
				<Static items={messages}>
					{(message, index) => (
						<Box
							paddingX={3}
							borderStyle={message.type == 'error' ? 'double' : 'classic'}
							borderColor={
								message.type === 'thought'
									? 'red'
									: message.type === 'tool'
									? 'yellow'
									: message.type === 'task'
									? 'red'
									: message.type === 'agent'
									? 'blue'
									: message.type === 'error'
									? 'red'
									: 'green'
							}
							key={index}
						>
							<Text
								key={index}
								color={
									message.type === 'thought'
										? 'red'
										: message.type === 'tool'
										? 'yellow'
										: message.type === 'task'
										? 'red'
										: message.type === 'agent'
										? 'blue'
										: message.type === 'error'
										? 'red'
										: 'green'
								}
							>
								{message.type === 'thought'
									? 'Devon is thinking: ' + message.text
									: message.type === 'tool'
									? 'Devon ran: ' + message.text
									: message.type === 'task'
									? 'Task: ' + message.text
									: message.type === 'agent'
									? 'Devon: ' + message.text
									: message.type === 'error'
									? 'Error: ' + message.text
									: 'User: ' + message.text}
							</Text>
						</Box>
					)}
				</Static>
				{status ? (
					<Box paddingX={3} marginBottom={1}>
						<Text>
							{status}
							{eventState.context.modelLoading || !state.matches('running') ? <Spinner type="simpleDots" /> : <></>}
						</Text>
					</Box>
				) : (
					<Box paddingX={3} marginBottom={1}></Box>
				)}

				<Box paddingX={3}>
					<TextInput
						value={inputValue}
						onChange={setInputValue}
						onSubmit={handleSubmit}
					/>
				</Box>
			</Box>
		</Box>
	);
};
