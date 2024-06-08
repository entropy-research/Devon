import React, { useEffect, useState } from 'react';
import {Box, Text, useInput, useApp, Static} from 'ink';
import TextInput from 'ink-text-input';
import axios from 'axios';
import Spinner from 'ink-spinner';
import {createActorContext, } from '@xstate/react';	
import {  newSessionMachine } from './state/server_manager.js';


const giveUserReponse = async (host: string, sessionName: string, res: string) => {
	try {
		const response = await axios.post(
			`${host}/session/${sessionName}/response?response=` + res,
		);
		return response.data;
	} catch (error: any) {
		console.error('Error:', error.message);
	}
};

type SessionEvent = {
	type: string;
	content: any;
	producer: string;
	consumer: string;
};

const sendSessionEvent = async (host: string, sessionName: string, event: SessionEvent) => {
	try {
		const response = await axios.post(
			`${host}/session/${sessionName}/event`,
			event,
		);
		return response.data;
	} catch (error: any) {
		// console.error('Error:', error.message);
	}
};

const SessionMachineContext = createActorContext(newSessionMachine);

export const App = ({port, reset, agentConfig} : {port : number, reset : boolean, agentConfig: any}) => {
	console.log("RESET: ", reset)
	return (
		<SessionMachineContext.Provider options={
			{
				input : {
					reset : reset,
					host : `http://localhost:${port}`,
					name : "123",
					path : process.cwd(),
				}
			}
		}>
			<Display agentConfig={agentConfig}/>
		</SessionMachineContext.Provider>
	);
};


const Display = ({ agentConfig }: { agentConfig: any}) => {
	const [inputValue, setInputValue] = useState('');
	let status = '';
	// const eventState = sessionState?.context.serverEventContext;
	const sessionState = SessionMachineContext.useSelector((state) => state);
	const sessionActor = SessionMachineContext.useActorRef()
	const eventState = sessionState?.context.serverEventContext;
	const {exit} = useApp();

	console.log("state",sessionState.value);
	if (!sessionState?.matches('running')) {
		status = 'Initializing...';
	} else if (eventState?.modelLoading) {
		status = 'Waiting for Devon...';
	} else if (eventState?.userRequest) {
		status = 'Type your message:';
	} else {
		status = 'Interrupt:';
	}

	useEffect(() => {
		sessionActor.send({ type: "session.begin", agentConfig: agentConfig})
	}, [])

	useInput((_: any, key: any) => {
		if (key.escape) {
			exit();
		}
	});

	const handleSubmit = () => {
		if (sessionState?.matches('running') && inputValue.trim() !== '') {
			setInputValue('');
			if (inputValue.toLowerCase() == 'exit') {
				exit();
			}
			if (inputValue.toLowerCase() == '/reset') {
				sendSessionEvent(sessionState?.context.host, sessionState?.context.name, {
					type: 'GitRequest',
					content: {
						type: 'revert_to_commit',
						commit_to_revert:
							eventState?.gitData.commits[
								eventState?.gitData.commits.length - 1
							],
						commit_to_go_to: eventState?.gitData.base_commit,
					},
					producer: 'cli',
					consumer: 'cli',
				});
			}

			if (eventState?.userRequest) {
				giveUserReponse(sessionState?.context.host, sessionState?.context.name, inputValue);
			} else {
				sendSessionEvent(sessionState?.context.host, sessionState?.context.name, {
					type: 'Interrupt',
					content: inputValue,
					producer: 'cli',
					consumer: 'cli',
				});
			}
		}
	};
	let messages = eventState?.messages || [];

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
							{eventState?.modelLoading || !sessionState?.matches('running') ? (
								<Spinner type="simpleDots" />
							) : (
								<></>
							)}
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
