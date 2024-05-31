import React, { useState } from 'react';
import ChatEditor from './ChatEditor';

const ChatWindow: React.FC = () => {
  const [messages, setMessages] = useState<string[]>([]);

  const handleSendMessage = (message: string) => {
    setMessages((prevMessages) => [...prevMessages, message]);
  };

  return (
    <div style={{ border: '1px solid #ccc', padding: '10px', width: '400px' }}>
      <div style={{ height: '300px', overflowY: 'scroll', marginBottom: '10px' }}>
        {messages.map((message, index) => (
          <div key={index} dangerouslySetInnerHTML={{ __html: message }} />
        ))}
      </div>
      <ChatEditor onSendMessage={handleSendMessage} />
    </div>
  );
};

export default ChatWindow;
