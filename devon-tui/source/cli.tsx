#!/usr/bin/env node
import React from 'react';
import {render} from 'ink';
// import meow from 'meow';
import {App} from './app.js';
import portfinder from 'portfinder';
import childProcess from 'node:child_process';
// import {writeLogLine} from './utils.js';

// TODO:
// - [ ] Task managment
// - [ ] package as a single executable

// - [x] style everything
// - [x] make output more compact
// - [x] anthropic key correctly
// - [x] Exit app on stop after user confirms
// - [x] make common exit function
// - [x] slow down and smooth new message rendering
// - [x] choose open port automatically
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

// check if anthropic key is set
if (!process.env['ANTHROPIC_API_KEY']) {
	console.log(
		'Please set the ANTHROPIC_API_KEY environment variable to use the Devon TUI.',
	);
	process.exit(1);
}

const controller = new AbortController();

portfinder.setBasePort(10000);
portfinder.getPort(function (_: any, port: number) {
	if (!childProcess.spawnSync('devon', ['--help']).stdout) {
		console.error(
			'The "devon" command is not available. Please ensure it is installed and in your PATH.',
		);
		process.exit(1);
	}

	const subProcess = childProcess.spawn(
		'devon',
		['server', '--port', port.toString()],
		{
			signal: controller.signal,
		},
	);

	// subProcess.stdout.on('data', (newOutput: Buffer) => {
	// 	writeLogLine(newOutput.toString('utf8'));
	// });

	// subProcess.stderr.on('data', (newOutput: Buffer) => {
	// 	console.error(newOutput.toString('utf8'));
	// });

	subProcess.on('error', error => {
		console.error('Error:', error.message);
		process.exit(0);
	});

	const {waitUntilExit} = render(<App port={port} />, {
		exitOnCtrlC: true,
	});

	waitUntilExit().then(() => {
		console.log('Exiting...');
		subProcess.kill();
		process.exit(0);
	});
});
