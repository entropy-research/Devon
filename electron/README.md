### 📚 Documentation

#### 📂 Structure

```
.
├── assets
│   ├── icon.icns
│   ├── icon.ico
│   └── icon.png
├── backend
│   ├── main.ts
│   ├── preload.ts
│   ├── README.md
│   ├── tsconfig.json
│   └── .eslintrc.json
├── frontend
│   ├── app
│   │   ├── assets
│   |   │   ├── edit.svg
│   |   │   └── menhera.png
│   │   ├── favicon.ico
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   ├── page.module.css
│   │   └── page.tsx
│   ├── context.d.ts
│   ├── .eslintrc.json
│   └── tsconfig.json
├── next.config.js
├── electron-builder.yml
├── package.json
├── README.md
└── yarn.lock

```

- `assets/`: Contains app icons used during run and build times.
- `backend/`: This is where your electron main processes reside.
- `frontend/`: This is where your NextJS app lives.
- `next.config.js`: NextJS config file.
- `electron-builder.yml`: Electron builder config file.

There's more information about `frontend` and `backend` parts in the README files in their respective directories.

&nbsp;

#### 💻 Scripts

First `yarn install` then:

You can run these scripts from your terminal using

```
yarn <SCRIPT_NAME>
```

<table> 
	<tr>
		<td> <pre>start</pre> </td>
		<td>Starts the app in development mode</td>
	</tr>
	<tr>
		<td> <pre>lint</pre> </td>
		<td>Checks for code styling issues with prettier, also runs eslint on backend and frontend</td>
	</tr>
	<tr>
		<td> <pre>lint:fix</pre> </td>
		<td>Formats code with prettier (write mode)</td>
	</tr>
	<tr>
		<td> <pre>storybook</pre> </td>
		<td>Starts the Storybook dev server</td>
	</tr>
	<tr>
		<td> <pre>build</pre> </td>
		<td>Builds the electron app (the `lint` script is auto-executed before building)</td>
	</tr>
	<tr>
		<td><pre>frontend:dev</pre></td>
		<td>Starts the NextJS development server</td>
	</tr>
	<tr>
		<td> <pre>frontend:lint</pre> </td>
		<td>Runs eslint only on the `frontend/` directory</td>
	</tr>
	<tr>
		<td> <pre>frontend:build</pre> </td>
		<td>Builds only the frontend NextJS app to `frontend/build/` directory</td>
	</tr>
	<tr>
		<td> <pre>backend:lint</pre> </td>
		<td>Runs eslint only on the `backend/` directory</td>
	</tr>
	<tr>
		<td> <pre>backend:build</pre> </td>
		<td>Transpiles the backend code to `backend/build/` directory</td>
	</tr>
</table>


## Attribution
[OpenDevin](https://github.com/OpenDevin/OpenDevin) for a few agent workspace items

[Vercel's `ai-chatbot`](https://github.com/vercel/ai-chatbot) for chat streaming

[NextJS-Electron-Boilerplate](https://github.com/DarkGuy10/NextJS-Electron-Boilerplate) for the Electron app template