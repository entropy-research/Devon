// vscode.ts

declare global {
    interface Window {
        acquireVsCodeApi(): {
            postMessage(message: unknown): void;
        };
    }
}
  
export const vscode = window.acquireVsCodeApi();