import React, { useEffect, useState } from 'react';
import { Box, Text, useInput, useApp, Static } from 'ink';
import TextInput from 'ink-text-input';
import Spinner from 'ink-spinner';
import { useMachine } from '@xstate/react';
import { newSessionMachine } from './sm.js';

export const App = ({ port, reset, agentConfig }: { port: number, reset: boolean, agentConfig: any }) => {

	const [sessionState, , sessionActor] = useMachine(newSessionMachine, {
		input: {
			reset: reset,
			host: `http://localhost:${port}`,
			name: "tui",
			path: process.cwd(),
		}
	});


	const [inputValue, setInputValue] = useState('');
	let status = '';
	const eventState = sessionState?.context.serverEventContext;
	const { exit } = useApp();
	let messages = eventState?.messages || [];
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
		sessionActor.subscribe((snapshot) => {
			if (snapshot.matches({
				"setup": "sessionDoesNotExist"
			})) {
				sessionActor.send({
					type: "session.create", payload: {
						agentConfig: agentConfig,
						path: process.cwd(),
					}
				})
			}
		})
	}, [])

	sessionActor.on("session.creationComplete", () => {
		if (reset) {
			sessionActor.send({ type: "session.delete" })
			reset = false
		}
		else {
			sessionActor.send({
				type: "session.init", payload: {
					agentConfig: agentConfig,
				}
			})
		}
	})




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

			sessionActor.send({ type: "session.sendMessage", message: inputValue })

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
