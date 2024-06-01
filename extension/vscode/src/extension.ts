import { commands, ExtensionContext } from "vscode";
import * as vscode from 'vscode';
import { ChatViewProvider } from './chatView';
import * as childProcess from 'child_process';
//@ts-ignore
import * as portfinder from 'portfinder';
import * as dotenv from 'dotenv';
import * as pathlib from 'path';

let serverProcess: childProcess.ChildProcess;


export function activate(context: vscode.ExtensionContext) {
  console.log(serverProcess)

  // Register commands
  const startCommand = vscode.commands.registerCommand('devon.start', startServer);
  const configureCommand = vscode.commands.registerCommand('devon.configure', configureExtension);
  console.log('Congratulations, your extension "devon" is now active!');
  // Create a sidebar view
  const sidebarProvider = new ChatViewProvider(context.extensionUri, startServer, configureExtension);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(ChatViewProvider.viewType, sidebarProvider,{
      webviewOptions: {
    }})

  );


  // Add commands to the extension context
  context.subscriptions.push(startCommand, configureCommand);

  context.subscriptions.push(new vscode.Disposable(() => {
    if (serverProcess) {
      serverProcess.kill(9);
      console.log('Server process killed');
    }
  }));
}



async function startServer() {
  // Get the configuration values
  // console.log(pathlib.join(vscode.workspace.workspaceFolders?.[0] as unknown as string, ".env"))
  // dotenv.config({ path: pathlib.join(vscode.workspace.workspaceFolders?.[0] as unknown as string, ".env") });
  const config = vscode.workspace.getConfiguration('devon');
  const apiKey = "sk-"
  const modelName = "gpt4-o";
  const apiBase = undefined;
  const promptType = undefined;

  console.log("Starting server");

  // Find an available port
  // const port = await portfinder.getPortPromise();

  const port = 8080;

  console.log(vscode.workspace.rootPath);

  // Spawn the server process
  try {
    serverProcess = childProcess.spawn(
      'devon_agent',
      [
        'server',
        '--port',
        port.toString(),
        '--model',
        modelName as string,
        '--api_key',
        apiKey as string,
        // '--api_base',
        // apiBase,
        // '--prompt_type',
        // promptType,
      ],
      {
        cwd: vscode.workspace.rootPath,
      }
    );

    console.log(serverProcess.pid);
    console.log(serverProcess.connected);
    // Handle server process output and errors
    serverProcess?.stdout?.on('data', (data: Buffer) => {
      console.log(data.toString());
      vscode.window.showInformationMessage(`Server output: ${data.toString()}`);
    });

    serverProcess?.stderr?.on('data', (data: Buffer) => {
      console.log(data.toString());
      vscode.window.showErrorMessage(`Server error: ${data.toString()}`);
    });
  } catch (error: any) {
    console.error('Error starting the server:', error);
    vscode.window.showErrorMessage(`Failed to start the server: ${error.message}`);
  }

  console.log("Spawned server");
}

function configureExtension() {
  // Show a configuration UI or open settings
  // Implement the configuration logic here
}

function getNonce() {
  let text = '';
  const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  for (let i = 0; i < 32; i++) {
    text += possible.charAt(Math.floor(Math.random() * possible.length));
  }
  return text;
}