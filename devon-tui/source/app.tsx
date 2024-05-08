import React, {useState} from 'react';
import {Box, Text, useInput, useApp, Static} from 'ink';
import TextInput from 'ink-text-input';
import axios from 'axios';
import Spinner from 'ink-spinner';
// import {writeLogLine} from './utils.js';

const createSession = async (port: number, path: string) => {
	let success = false;
	while (!success) {
		try {
			const encodedPath = encodeURIComponent(path);
			const response = await axios.post(
				`http://localhost:${port}/session?session=cli&path=${encodedPath}`,
			);
			return response;
		} catch (error: any) {
			await new Promise(resolve => setTimeout(resolve, 1000)); // Wait for 1 second before retrying
		}
	}
	return false;
};

const startSession = async (
	port: number,
	setStarted: (value: boolean) => void,
) => {
	let success = false;
	while (!success) {
		try {
			const response = await axios.post(
				`http://localhost:${port}/session/cli/start`,
			);
			setStarted(true);
			return response.data;
		} catch (error: any) {
			await new Promise(resolve => setTimeout(resolve, 1000)); // Wait for 1 second before retrying
		}
	}
};

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

type Event = {
	type:
		| 'ModelResponse'
		| 'ToolResponse'
		| 'Task'
		| 'Interrupt'
		| 'UserRequest'
		| 'Stop'
		| 'EnvironmentRequest'
		| 'EnvironmentResponse'
		| 'ModelRequest'
		| 'ToolRequest'
		| 'UserResponse';
	content: string;
	identifier: string | null;
};

type Message = {
	text: string;
	type: 'user' | 'agent' | 'command' | 'tool' | 'task' | 'thought';
};

const handleEvents = (
	events: Event[],
	setUserRequested: (value: boolean) => void,
	setModelLoading: (value: boolean) => void,
	exit: () => void,
) => {
	const messages: Message[] = [];
	let user_request = false;
	let model_loading = false;
	let tool_message = '';
	let idx = 0;

	for (const event of events) {
		if (event.type == 'ModelRequest') {
			model_loading = true;
		}

		if (event.type == 'ModelResponse') {
			let content = JSON.parse(event.content);
			model_loading = false;
			messages.push({text: content.thought, type: 'thought'});
		}

		if (event.type == 'EnvironmentRequest') {
			tool_message = 'Running command: ' + event.content;
		}

		if (event.type == 'EnvironmentResponse') {
			tool_message += '\n> ' + event.content;
			if (tool_message.length > 2000) {
				messages.push({text: tool_message.slice(0, 2000), type: 'tool'});
			} else {
				messages.push({text: tool_message, type: 'tool'});
			}
			tool_message = '';
		}

		if (event.type == 'Task') {
			messages.push({text: event.content, type: 'task'});
		}

		if (event.type == 'Interrupt') {
			// writeLogLine('interrupt: ' + event.content);
			messages.push({text: event.content, type: 'user'});
		}

		if (event.type == 'UserResponse') {
			messages.push({text: event.content, type: 'user'});
			user_request = false;
		}

		if (event.type == 'UserRequest') {
			messages.push({text: event.content, type: 'agent'});
			user_request = true;
		}

		if (event.type == 'Stop') {
			console.log('Devon has left the chat.');
			exit();
		}
		idx += 1;
	}
	setUserRequested(user_request);
	setModelLoading(model_loading);
	return messages;
};

export const App = ({port}: {port: number}) => {
	const [messages, setMessages] = useState<Message[]>([]);
	const [inputValue, setInputValue] = useState('');
	const [userRequested, setUserRequested] = useState(false);
	const [modelLoading, setModelLoading] = useState(false);
	const [started, setStarted] = useState(false);
	let status = '';

	const {exit} = useApp();
	let eventI = 0;

	if (!started) {
		status = 'Initializing...';
	} else if (modelLoading) {
		status = 'Waiting for Devon...';
	} else if (userRequested) {
		status = 'Type your message:';
	} else {
		status = 'Interrupt:';
	}

	React.useEffect(() => {
		let cwd = process.cwd();
		createSession(port, cwd);
		startSession(port, setStarted);

		const interval = setInterval(async () => {
			const newEvents = await fetchEvents(port);
			if (newEvents) {
				const newMessages = handleEvents(
					newEvents,
					setUserRequested,
					setModelLoading,
					exit,
				);
				for (let i = eventI; i < newMessages.length; i++) {
					setMessages(messages => [...messages, newMessages[i] as Message]);
					eventI++;
					await new Promise(resolve => setTimeout(resolve, 500));
				}
			}
		}, 1000);

		return () => clearInterval(interval);
	}, []);

	useInput((_: any, key: any) => {
		if (key.escape) {
			exit();
		}
	});

	const handleSubmit = () => {
		if (started && inputValue.trim() !== '') {
			setInputValue('');
			if (inputValue.toLowerCase() == 'exit') {
				exit();
			}

			if (userRequested) {
				giveUserReponse(port, inputValue);
				setUserRequested(false);
			} else {
				sendInterrupt(port, inputValue);
			}
		}
	};

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
							borderStyle="classic"
							borderColor={
								message.type === 'thought'
									? 'red'
									: message.type === 'tool'
									? 'yellow'
									: message.type === 'task'
									? 'red'
									: message.type === 'agent'
									? 'blue'
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
									: 'User: ' + message.text}
							</Text>
						</Box>
					)}
				</Static>
				{status ? (
					<Box paddingX={3} marginBottom={1}>
						<Text>
							{status}
							{modelLoading || !started ? <Spinner type="simpleDots" /> : <></>}
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
