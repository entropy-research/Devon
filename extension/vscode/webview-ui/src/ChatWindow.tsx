import React, { useState } from 'react';
import ChatEditor from './ChatEditor';
import { useMachine } from '@xstate/react';
import { sessionMachine } from './sm';
import axios from 'axios';
import { vscode } from './vscode';
import {v4} from 'uuid';

const giveUserResponse = async (res: string) => {
  try {
    const response = await axios.post(`http://localhost:8080/session/cli/response?response=${res}`);
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

const sendSessionEvent = async (event: SessionEvent) => {
  try {
    const response = await axios.post(`http://localhost:8080/session/cli/event`, event);
    return response.data;
  } catch (error: any) {
    // console.error('Error:', error.message);
  }
};

const ChatWindow: React.FC = () => {
  const [inputValue, setInputValue] = useState('');
  const [state] = useMachine(sessionMachine, {
    input: {
      host: 'http://0.0.0.0:8080',
      name: v4(),
      path: "/",
      reset: true,
    },
  });

  const eventState = state.context.serverEventContext;
  let status = '';

  if (!state.matches('running')) {
    status = 'Initializing...';
  } else if (eventState.modelLoading) {
    status = 'Waiting for Devon...';
  } else if (eventState.userRequest) {
    status = 'Type your message:';
  } else {
    status = 'Interrupt:';
  }

  const handleSendMessage = (message: string) => {
    setInputValue(message);
    if (state.matches('running') && message.trim() !== '') {
      if (message.toLowerCase() === 'exit') {
        vscode.postMessage({ command: 'exit' });
      }
      if (message.toLowerCase() === '/reset') {
        sendSessionEvent({
          type: 'GitRequest',
          content: {
            type: 'revert_to_commit',
            commit_to_revert: eventState.gitData.commits[eventState.gitData.commits.length - 1],
            commit_to_go_to: eventState.gitData.base_commit,
          },
          producer: 'cli',
          consumer: 'cli',
        });
      }

      if (eventState.userRequest) {
        giveUserResponse(message);
      } else {
        sendSessionEvent({
          type: 'Interrupt',
          content: message,
          producer: 'cli',
          consumer: 'cli',
        });
      }
    }
  };

  return (
    <div style={{ border: '1px solid #ccc', padding: '10px', width: '400px' }}>
      <div style={{ height: '300px', overflowY: 'scroll', marginBottom: '10px' }}>
        {eventState.messages.map((message: any, index: number) => (
          <div
            key={index}
            style={{
              borderStyle: message.type === 'error' ? 'double' : 'solid',
              borderColor:
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
                  : 'green',
              color:
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
                  : 'green',
            }}
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
          </div>
        ))}
      </div>
      <ChatEditor onSendMessage={handleSendMessage} status={status} eventState={eventState} />
    </div>
  );
};

export default ChatWindow;
