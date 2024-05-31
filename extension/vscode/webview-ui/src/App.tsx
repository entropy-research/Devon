import * as vscode from "vscode"
import { VSCodeButton } from "@vscode/webview-ui-toolkit/react";
import "./App.css";
import ChatWindow from "./ChatWindow";

function App() {

  return (
    <main>
      <ChatWindow />
    </main>
  );
}

export default App;
