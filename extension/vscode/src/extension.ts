import { commands, ExtensionContext } from "vscode";
import * as vscode from 'vscode';
import { ChatViewProvider } from './chatView';
import * as childProcess from 'child_process';
//@ts-ignore
import * as portfinder from 'portfinder';

export function activate(context: vscode.ExtensionContext) {
  // Register commands
  const startCommand = vscode.commands.registerCommand('devon.start', startServer);
  const configureCommand = vscode.commands.registerCommand('devon.configure', configureExtension);

  // Create a sidebar view
  const sidebarProvider = new ChatViewProvider(context.extensionUri, startServer, configureExtension);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(ChatViewProvider.viewType, sidebarProvider)
  );

  // Add commands to the extension context
  context.subscriptions.push(startCommand, configureCommand);
}

async function startServer() {
  // Get the configuration values
  const config = vscode.workspace.getConfiguration('devon');
  const apiKey = config.get('apiKey') as string;
  const modelName = config.get('modelName') as string;
  const apiBase = config.get('apiBase') as string;
  const promptType = config.get('promptType') as string;

  console.log("Starting server")

  // Find an available port
  // const port = await portfinder.getPortPromise();

  const port = 8080

  // Spawn the server process
  try {
    const serverProcess = childProcess.spawn(
      'devon_agent',
      [
        'server',
        '--port',
        port.toString(),
        '--model',
        modelName,
        '--api_key',
        apiKey,
        '--api_base',
        apiBase,
        '--prompt_type',
        promptType,
      ],
      {
        cwd: vscode.workspace.rootPath,
      }
    );

    console.log(serverProcess.pid)
    // Handle server process output and errors
    serverProcess.stdout.on('data', (data: Buffer) => {
      vscode.window.showInformationMessage(`Server output: ${data.toString()}`);
    });

    serverProcess.stderr.on('data', (data: Buffer) => {
      vscode.window.showErrorMessage(`Server error: ${data.toString()}`);
    });
  } catch (error: any) {
    console.error('Error starting the server:', error);
    vscode.window.showErrorMessage(`Failed to start the server: ${error.message}`);
  }

  console.log("Spawned server")
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