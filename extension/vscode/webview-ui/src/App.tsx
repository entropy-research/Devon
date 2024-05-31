import { vscode } from './vscode';
import React, { useEffect } from 'react';
import './App.css';
import ChatWindow from './ChatWindow';

function App() {
  useEffect(() => {
    console.log('starting server');

    vscode.postMessage({ command: 'startServer' });
  }, []);

  return (
    <main>
      <ChatWindow />
    </main>
  );
}

export default App;