# Backend

This will handle the electron main process.

`main.ts` is the default entry point for the main process.

`preload.ts` should contain the preload scripts. Here's [something](https://www.electronjs.org/docs/latest/tutorial/tutorial-preload) to get you started with. Make sure to add proper typings for the APIs exposed over the context bridge in `frontend/context.d.ts`.

> [!TIP]
> You can provide and use path aliases for main process in the `tsconfig.json` file in this directory. `tsc-alias` will automatically transpile them.
