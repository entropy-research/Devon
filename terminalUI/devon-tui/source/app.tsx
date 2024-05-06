import React, { useState, useRef } from 'react';
import {  Box, Text, useInput, useApp } from 'ink';
import TextInput from 'ink-text-input';
import childProcess from 'node:child_process';
import axios from 'axios';
import fs from 'fs';

const LOG_FILE = "./devon-tui.log"

const fd = fs.openSync(LOG_FILE, 'a');

const writeLogLine = (line: string) => {
    try {
        fs.appendFileSync(fd, line + "\n");
    } catch (error) {
        console.error("Failed to write to log file:", error);
    }
}

const createSession = async (path:string) => {
  let success = false;
  while (!success) {
    try {
      const encodedPath = encodeURIComponent(path);
      const response = await axios.post(`http://localhost:8000/session?session=cli&path=${encodedPath}`);
      return response
      success = true;
    } catch (error: any) {
      console.error('Error:', error.message);
      await new Promise(resolve => setTimeout(resolve, 1000)); // Wait for 1 second before retrying
    }
  }
  return false
};

const startSession = async () => {
  let success = false;
  while (!success) {
    try {
      const response = await axios.post('http://localhost:8000/session/cli/start');
    //   console.log(response.data);
	return response.data
      success = true;
    } catch (error: any) {
      console.error('Error starting session:', error.message);
      await new Promise(resolve => setTimeout(resolve, 1000)); // Wait for 1 second before retrying
    }
  }
};


const fetchEvents = async () => {
  try {
    const response = await axios.get('http://localhost:8000/session/cli/events');
    return response.data;
  } catch (error: any) {
    console.error('Error:', error.message);
  }
};


const giveUserReponse = async (res: string) => {
	try {
		const response = await axios.post('http://localhost:8000/session/cli/response?response=' + res);
		return response.data;
	} catch (error: any) {
		console.error('Error:', error.message);
	}
}

const sendInterrupt = async (res: string) => {
	try {
		writeLogLine("interrupt: " + res)
		const response = await axios.post('http://localhost:8000/session/cli/interrupt?message=' + res);
		return response.data;
	} catch (error: any) {
		console.error('Error:', error.message);
	}
}

type Event = {
	type: "ModelResponse" | "ToolResponse" | "Task" | "Interrupt" | "UserRequest" | "Stop" | "EnvironmentRequest" | "EnvironmentResponse" | "ModelRequest" | "ToolRequest" | "UserResponse",
	content: string,
	identifier: string | null
}

type Message = {
	text: string,
	type: "user" | "agent" | "command" | "tool" | "task"
}


const handleEvents = (events: Event[], setUserRequested: (value: boolean) => void) => {
	const messages : Message[] = []
	let user_request = false;

	for (const event of events) {
		// console.log("EVENT", event["content"]);
		if (event.type == "ModelResponse") {
			
			let content  = JSON.parse(event.content);

			messages.push({text: content.thought, type: "agent"});
		}

		if (event.type == "EnvironmentRequest") {
			messages.push({text: "Running command: " + event.content, type: "tool"});
		}

		if (event.type == "EnvironmentResponse") {
			messages.push({text: "> " + event.content, type: "tool"});
		}
	
		if (event.type == "Task") {
			messages.push({text: event.content, type: "task"});
		}

		if (event.type == "Interrupt") {
			writeLogLine("interrupt: " + event.content)	
			messages.push({text: event.content, type: "user"});
		}

		if (event.type == "UserResponse") {
			messages.push({text: event.content, type: "user"});
			user_request = false
		}

		if (event.type == "UserRequest") {
			messages.push({text: event.content, type: "agent"});
			user_request = true
		}
 
	}
	setUserRequested(user_request);
	return messages
}




export const App = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [userRequested, setUserRequested] = useState(false);
  const { exit } = useApp();
  const scrollRef = useRef(null);

//   const [events, setEvents] = useState<Event[]>([]);


  React.useEffect(() => {
	const subProcess = childProcess.spawn('python3', [
		'/Users/mihirchintawar/agent/devon/environment/server.py',
	]);

	subProcess.stdout.on('data', (newOutput: Buffer) => {
		writeLogLine(newOutput.toString('utf8')); 

	});

	subProcess.stderr.on('data', (newOutput: Buffer) => {
		console.error(newOutput.toString('utf8'));
	});


}, []);

	React.useEffect(() => {

		let cwd = process.cwd();
		createSession(cwd);
		startSession();
		// console.log("Started session");
	
	const interval = setInterval(async () => {
		const newEvents = await fetchEvents();
		// console.log("NEW EVENTS", newEvents);

		// setEvents(newEvents);
		if (newEvents) {
			const newMessages = handleEvents(newEvents, setUserRequested);
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

  useInput((_ : any, key : any) => {
    if (key.escape) {
      exit();
    }
  });

  const handleSubmit = () => {
    if (inputValue.trim() !== '') {
      setMessages([...messages, { text: inputValue, type: "user" }]);
      setInputValue('');

      if (userRequested) {
		giveUserReponse(inputValue);
        setUserRequested(false);
      }
	  else {
		sendInterrupt(inputValue);
      }
    }
  };

  return (
    <Box flexDirection="column" height="100%" borderStyle="round" borderColor="white">
      {/* <Box flexGrow={1} overflow="hidden"> */}
        <Box flexDirection="column" paddingX={1} paddingY={1}>
          {messages.map((message, index) => {

			let displayText = message.text;
			let borderColor = "blue";
			if (message.type == "command") {
				displayText = "Command: " + message.text;
				borderColor = "green";
			}
			if (message.type == "tool") {
				displayText = "Tool: " + message.text;
				borderColor = "yellow";
			}
			if (message.type == "task") {
				displayText = "Tasksfaf: " + message.text;
				borderColor = "red";
			}
			if (message.type == "agent") {
				displayText = "Agent: " + message.text;
				borderColor = "blue";
			}
			if (message.type == "user") {
				displayText = "User: " + message.text;
				borderColor = "green";
			}
			return <Box paddingRight={message.type == "user" ? 10 : 0} borderStyle="round" borderColor={borderColor} key={index}>            
			<Text key={index} color={borderColor}>
              {displayText}
            </Text>
			</Box>
})}
          <Box ref={scrollRef} />
        {/* </Box> */}
      </Box>
      <Box paddingX={2} paddingY={1} borderStyle="round" borderColor="white">
        <TextInput

          value={inputValue}
          onChange={setInputValue}
          onSubmit={handleSubmit}
          placeholder="Type your message..."
        />
      </Box>
    </Box>
  );
};

// render(<ChatInterface />);