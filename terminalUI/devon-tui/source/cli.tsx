#!/usr/bin/env node
import React from 'react';
import {render} from 'ink';
// import meow from 'meow';
import {App} from './app.js';

// TODO:
// - [x] Fix interrupt
// - [x] Add loading/ feedback for user
// - [ ] Task managment
// - [x] Start Loading Screen 
// - [ ] Exit app on stop after user confirms
// - [x] combine command and output into one
// - [ ] provide headless mode
// - [ ] slow down and smooth new message rendering
// - [ ] paginate outputs
// - [ ] deliniate between agent thoughts and agent questions
// - [ ] handle error output 
// - [ ] handle debug console
// - [ ] choose open port automatically
// - [ ] make output more compact
// - [ ] if window big show editor and cli
// - [ ] anthropic key correctly



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

render(<App />,{
	exitOnCtrlC: true,
});

