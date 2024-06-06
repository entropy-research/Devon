import React, {createContext, useContext, useState} from 'react';
import {Box, Text, useInput, useApp, Static} from 'ink';
import TextInput from 'ink-text-input';
import axios from 'axios';
import Spinner from 'ink-spinner';
import {useMachine, useSelector, } from '@xstate/react';	
import { serverMachine, sessionMachine } from './state/server_manager.js';
import { ActorRefFrom } from 'xstate';


const giveUserReponse = async (port: number, res: string) => {
	try {
		const response = await axios.post(
			`http://localhost:${port}/session/cli/response?response=` + res,
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

const sendSessionEvent = async (port: number, event: SessionEvent) => {
	try {
		const response = await axios.post(
			`http://localhost:${port}/session/cli/event`,
			event,
		);
		return response.data;
	} catch (error: any) {
		// console.error('Error:', error.message);
	}
};


const SessionManagerContext = createContext<{
	activeSession : string | undefined,
	setActiveSession: any,
	sessionMap : Map<string, ActorRefFrom<typeof sessionMachine>>,
}>({
	activeSession : "123",
	setActiveSession: undefined,
	sessionMap : new Map<string, ActorRefFrom<typeof sessionMachine>>(),
});

type SessionProps = {
	reset : boolean,
	sessionName : string,
	path : string
}

const SessionManagerProvider = ({ children, port, session}: { children: React.ReactNode; port: number, session: SessionProps }) => {
    // const [sessionManager] = useState<SessionManager>(new SessionManager(`http://localhost:${port}`));
	const [activeSession, setActiveSession] =  useState<string | undefined>(undefined);

	const [state, send] = useMachine(serverMachine, { id: "serverMachine", input: { host: `http://localhost:${port}` }});

	send({type: "server.setup"})
	send({
		type: "server.spawnSession",
		payload: {
			...session, 
			sessionId: session.sessionName, 
			apiKey: ""
		}
	})

    return (
        <SessionManagerContext.Provider value={{
			activeSession: activeSession,
			setActiveSession: setActiveSession,
			sessionMap : state.context.refs,
		}}>
            {state.context.refs ? children : null}
        </SessionManagerContext.Provider>
    );
};


export const App = ({port, reset} : {port : number, reset : boolean}) => {

	return (
		<SessionManagerProvider  port={port} session={
			{
				sessionName : "123",
				path : process.cwd(),
				reset : reset
			}
		}>
			<Display port={port}/>
		</SessionManagerProvider>
	);
};


const Display = ({port} : {port : number}) => {
	const [inputValue, setInputValue] = useState('');
	let status = '';
	const {activeSession, sessionMap} = useContext(SessionManagerContext);
	let sessionState = useSelector(sessionMap.get(activeSession ?? "123"), (snapshot) => snapshot);
	const eventState = sessionState?.context.serverEventContext;
	const {exit} = useApp();

	// console.log("state",sessionState);
	if (!sessionState?.matches('running')) {
		status = 'Initializing...';
	} else if (eventState?.modelLoading) {
		status = 'Waiting for Devon...';
	} else if (eventState?.userRequest) {
		status = 'Type your message:';
	} else {
		status = 'Interrupt:';
	}

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
				sendSessionEvent(port, {
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
				giveUserReponse(port, inputValue);
			} else {
				sendSessionEvent(port, {
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
