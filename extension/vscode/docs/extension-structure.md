# Extension structure

This section provides a quick introduction into how this sample extension is organized and structured.

The two most important directories to take note of are the following:

- `src`: Contains all of the extension source code
- `webview-ui`: Contains all of the webview UI source code

## `src` directory

The `src` directory contains all of the extension-related source code and can be thought of as containing the "backend" code/logic for the entire extension. Inside of this directory you'll find the:

- `panels` directory
- `utilities` directory
- `extension.ts` file

The `panels` directory contains all of the webview-related code that will be executed within the extension context. It can be thought of as the place where all of the "backend" code for each webview panel is contained.

This directory will typically contain individual TypeScript or JavaScript files that contain a class which manages the state and behavior of a given webview panel. Each class is usually in charge of:

- Creating and rendering the webview panel
- Properly cleaning up and disposing of webview resources when the panel is closed
- Setting message listeners so data can be passed between the webview and extension
- Setting the initial HTML markdown of the webview panel
- Other custom logic and behavior related to webview panel management

As the name might suggest, the `utilties` directory contains all of the extension utility functions that make setting up and managing an extension easier. In this case, it contains `getUri.ts` which contains a helper function which will get the webview URI of a given file or resource.

Finally, `extension.ts` is where all the logic for activating and deactiving the extension usually live. This is also the place where extension commands are registered.

## `webview-ui` directory

The `webview-ui` directory contains all of the React-based webview source code and can be thought of as containing the "frontend" code/logic for the extension webview.

This directory is special because it contains a full-blown React application which was created using the TypeScript [Vite](https://vitejs.dev/) template. As a result, `webview-ui` contains its own `package.json`, `node_modules`, `tsconfig.json`, and so on––separate from the `hello-world` extension in the root directory.

This strays a bit from other extension structures, in that you'll usually find the extension and webview dependencies, configurations, and source code more closely integrated or combined with each other.

However, in this case, there are some unique benefits and reasons for why this sample extension does not follow those patterns such as easier management of conflicting dependencies and configurations, as well as the ability to use the Vite dev server, which drastically improves the speed of developing your webview UI, versus recompiling your extension code every time you make a change to the webview.
