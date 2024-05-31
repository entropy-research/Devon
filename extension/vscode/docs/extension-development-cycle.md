# Extension development cycle

The intended development cycle of this React-based webview extension is slightly different than that of other VS Code extensions.

Due to the fact that the `webview-ui` directory holds a self-contained React application we get to take advantage of some of the perks that that enables. In particular,

- UI development and iteration cycles can happen much more quickly by using Vite
- Dependency management and project configuration is hugely simplified

## UI development cycle

Since we can take advantage of the much faster Vite dev server, it is encouraged to begin developing webview UI by running the `npm run start:webview` command and then editing the code in the `webview-ui/src` directory.

_Tip: Open the command palette and run the `Simple Browser` command and fill in `http://localhost:3000/` when prompted. This will open a simple browser environment right inside VS Code._

### Message passing
If you need to implement message passing between the webview context and extension context via the VS Code API, a helpful utility is provided in the `webview-ui/src/utilities/vscode.ts` file.

This file contains a utility wrapper around the `acquireVsCodeApi()` function, which enables message passing and state management between the webview and extension contexts.

This utility also enables webview code to be run in the Vite dev server by using native web browser features that mock the functionality enabled by acquireVsCodeApi. This means you can keep building your webview UI with the Vite dev server even when using the VS Code API.

### Move to traditional extension development
Once you're ready to start building other parts of your extension, simply shift to a development model where you run the `npm run build:webview` command as you make changes, press `F5` to compile your extension and open a new Extension Development Host window. Inside the host window, open the command palette (`Ctrl+Shift+P` or `Cmd+Shift+P` on Mac) and type `Hello World (React + Vite): Show`.

## Dependency management and project configuration

As mentioned above, the `webview-ui` directory holds a self-contained and isolated React application meaning you can (for the most part) treat the development of your webview UI in the same way you would treat the development of a regular React application.

To install webview-specific dependencies simply navigate (i.e. `cd`) into the `webview-ui` directory and install any packages you need or set up any React specific configurations you want.
