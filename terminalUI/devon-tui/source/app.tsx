import React, {useState} from 'react';
import {Box, Text, useInput, useApp} from 'ink';
import TextInput from 'ink-text-input';
import childProcess from 'node:child_process';
import axios from 'axios';
import Spinner from 'ink-spinner';
import fs from 'fs';

const LOG_FILE = './devon-tui.log';

const fd = fs.openSync(LOG_FILE, 'a');

const writeLogLine = (line: string) => {
	try {
		fs.appendFileSync(fd, line + '\n');
	} catch (error) {
		// console.error('Failed to write to log file:', error);
	}
};

const createSession = async (path: string) => {
	let success = false;
	while (!success) {
		try {
			const encodedPath = encodeURIComponent(path);
			const response = await axios.post(
				`http://localhost:8000/session?session=cli&path=${encodedPath}`,
			);
			return response;
			success = true;
		} catch (error: any) {
			// console.error('Error:', error.message);
			await new Promise(resolve => setTimeout(resolve, 1000)); // Wait for 1 second before retrying
		}
	}
	return false;
};

const startSession = async (setStarted: (value: boolean) => void) => {
	let success = false;
	while (!success) {
		try {
			const response = await axios.post(
				'http://localhost:8000/session/cli/start',
			);
			//   console.log(response.data);
			setStarted(true);
			return response.data;
			success = true;
		} catch (error: any) {
			// console.error('Error starting session:', error.message);
			await new Promise(resolve => setTimeout(resolve, 1000)); // Wait for 1 second before retrying
		}
	}
};

const fetchEvents = async () => {
	try {
		const response = await axios.get(
			'http://localhost:8000/session/cli/events',
		);
		return response.data;
	} catch (error: any) {
		// console.error('Error:', error.message);
	}
};

const giveUserReponse = async (res: string) => {
	try {
		const response = await axios.post(
			'http://localhost:8000/session/cli/response?response=' + res,
		);
		return response.data;
	} catch (error: any) {
		// console.error('Error:', error.message);
	}
};

const sendInterrupt = async (res: string) => {
	try {
		writeLogLine('interrupt: ' + res);
		const response = await axios.post(
			'http://localhost:8000/session/cli/interrupt?message=' + res,
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
	type: 'user' | 'agent' | 'command' | 'tool' | 'task';
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
	let tool_message = ""

	for (const event of events) {
		// console.log("EVENT", event["content"]);
		if (event.type == 'ModelRequest') {
			model_loading = true;
		}

		if (event.type == 'ModelResponse') {
			let content = JSON.parse(event.content);
			model_loading = false;
			messages.push({text: content.thought, type: 'agent'});
		}

		if (event.type == 'EnvironmentRequest') {
			tool_message = "Running command: " + event.content;
		}

		if (event.type == 'EnvironmentResponse') {
			tool_message += '\n> ' + event.content
			messages.push({text: tool_message, type: 'tool'});
			tool_message = ""
		}

		if (event.type == 'Task') {
			messages.push({text: event.content, type: 'task'});
		}

		if (event.type == 'Interrupt') {
			writeLogLine('interrupt: ' + event.content);
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
			exit();
		}
	}
	setUserRequested(user_request);
	setModelLoading(model_loading);
	return messages;
};

export const App = () => {
	const [messages, setMessages] = useState<Message[]>([]);
	const [inputValue, setInputValue] = useState('');
	const [userRequested, setUserRequested] = useState(false);
	const [modelLoading, setModelLoading] = useState(false);
	const [started,setStarted] = useState(false);
	const {exit} = useApp();
	// const scrollRef = useRef(null);
	const controller = new AbortController();


	//   const [events, setEvents] = useState<Event[]>([]);

	React.useEffect(() => {
		const subProcess = childProcess.spawn('python3', [
			'/Users/mihirchintawar/agent/devon/environment/server.py',
		],{
			signal: controller.signal
		});

		subProcess.stdout.on('data', (newOutput: Buffer) => {
			writeLogLine(newOutput.toString('utf8'));
		});

		// subProcess.stderr.on('data', (newOutput: Buffer) => {
			// console.error(newOutput.toString('utf8'));
		// });

		subProcess.on("error", (error) => {
			console.error('Error:', error.message);
			process.exit(0);
		});


	}, []);

	React.useEffect(() => {
		let cwd = process.cwd();
		createSession(cwd);
		startSession(setStarted);
		// console.log("Started session");

		const interval = setInterval(async () => {
			const newEvents = await fetchEvents();
			// console.log("NEW EVENTS", newEvents);

			// setEvents(newEvents);
			if (newEvents) {
				const newMessages = handleEvents(newEvents, setUserRequested,setModelLoading,exit);
				setMessages(newMessages);
			}

			// console.log("MESSAGES", messages);
		}, 1000);

		return () => clearInterval(interval);
	}, []);

	//   useEffect(() => {
	//     if (scrollRef.current) {
	//       (scrollRef.current as any).scrollIntoView({ behavior: 'smooth' });
	//     }
	//   }, [messages]);

	useInput((_: any, key: any) => {
		if (key.escape) {
			exit();
		}
	});

	const handleSubmit = () => {
		if (started &&inputValue.trim() !== '') {
			setMessages([...messages, {text: inputValue, type: 'user'}]);
			setInputValue('');
			if (inputValue.toLowerCase() == 'exit') {

				controller.abort();
				exit();
				process.exit(0);
			}

			if (userRequested) {
				giveUserReponse(inputValue);
				setUserRequested(false);
			} else {
				sendInterrupt(inputValue);
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
			{/* <Box flexGrow={1} overflow="hidden"> */}
			<Box flexDirection="column" overflowX="hidden" paddingX={1} paddingY={1}>
				{!started && <Text>Initializing...<Spinner type="simpleDots" /></Text>}
				{messages.map((message, index) => {
					let displayText = message.text;
					let borderColor = 'blue';
					if (message.type == 'command') {
						displayText = 'Command: ' + message.text;
						borderColor = 'green';
					}
					if (message.type == 'tool') {
						displayText = 'Tool: ' + message.text;
						borderColor = 'yellow';
					}
					if (message.type == 'task') {
						displayText = 'Tasksfaf: ' + message.text;
						borderColor = 'red';
					}
					if (message.type == 'agent') {
						displayText = 'Agent: ' + message.text;
						borderColor = 'blue';
					}
					if (message.type == 'user') {
						displayText = 'User: ' + message.text;
						borderColor = 'green';
					}
					return (
						<Box
							paddingX={3}
							borderStyle="classic"
							borderColor={borderColor}
							key={index}
						>
							<Text key={index} color={borderColor}>
								{displayText}
							</Text>
						</Box>
					);
				})}
				{modelLoading && <Box paddingX={3}>
					<Text>Waiting for Agent...</Text>
					<Spinner type="simpleDots" />
				</Box>}
				{/* <Box ref={scrollRef} /> */}
				{/* </Box> */}
			</Box>
			{/* <Box  borderStyle="round" borderTopColor="white"> */}
			{/* <Box paddingX={2} paddingY={1} borderStyle="round" borderColor="white"> */}
				<TextInput

					value={inputValue}
					onChange={setInputValue}
					onSubmit={handleSubmit}
					placeholder="Type your message..."
				/>
			{/* </Box> */}
		 </Box>
	);
};

// render(<ChatInterface />);
