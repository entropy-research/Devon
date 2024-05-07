#!/usr/bin/env node
import React from 'react';
import {render} from 'ink';
// import meow from 'meow';
import {App} from './app.js';
import portfinder from 'portfinder';
// TODO:

// - [ ] anthropic key correctly
// - [ ] Task managment
// - [ ] Exit app on stop after user confirms
// - [ ] slow down and smooth new message rendering
// - [ ] choose open port automatically
// - [ ] make output more compact
// - [x] deliniate between agent thoughts and agent questions
// - [x] Fix interrupt
// - [x] Add loading/ feedback for user
// - [x] Start Loading Screen 
// - [x] combine command and output into one


// - [ ] provide headless mode
// - [ ] handle error output 
// - [ ] handle debug console
// - [ ] if window big show editor and cli
// - [ ] paginate outputs

// const cli = meow(
// 	`
// 	Usage
// 	  $ devon-tui

// 	Options
// 		--name  Your name

// 	Examples
// 	  $ devon-tui --name=Jane
// 	  Hello, Jane
// `,
// 	{
// 		importMeta: import.meta,
// 		flags: {
// 			name: {
// 				type: 'string',
// 			},
// 		},
// 	},
// );
portfinder.getPort(function (_ : any, port : number) {

render(<App port={port} />,{
	exitOnCtrlC: true,
})
})