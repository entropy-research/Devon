#!/usr/bin/env node
import React from 'react';
import {render} from 'ink';
// import meow from 'meow';
import { App } from './app.js';

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

render(<App  />);
