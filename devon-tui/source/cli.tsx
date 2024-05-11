#!/usr/bin/env node
import React from 'react';
import {render} from 'ink';
// import meow from 'meow';
import {App} from './app.js';
import portfinder from 'portfinder';
import childProcess from 'node:child_process';
import {writeLogLine} from './utils.js';



// import {writeLogLine} from './utils.js';

// TODO:
// - [ ] provide headless mode
// - [ ] handle error output
// - [ ] handle debug console
// - [ ] if window big show editor and cli
// - [ ] paginate outputs

// const cli = meow(
// 	`
// 	Usage
// 	  $ devon

// 	Options
// 	  --version  Show version

// 	Examples
// 	  $ devon
// `,
// 	{
// 		importMeta: import.meta,
// 		flags: {
// 			version: {
// 				type: 'boolean',
// 				alias: 'v',
// 			},
// 		},
// 	},
// );

// if (cli.flags.version) {
// 	console.log(cli.pkg.version);
// 	process.exit(0);
// }



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
	if (!childProcess.spawnSync('devon_agent', ['--help']).stdout) {
		console.error(
			'The "devon" command is not available. Please ensure it is installed and in your PATH.',
		);
		process.exit(1);
	}

	const subProcess = childProcess.spawn(
		'devon_agent',
		['server', '--port', port.toString()],
		{
			signal: controller.signal,
		},
	);

	subProcess.stdout.on('data', (newOutput: Buffer) => {
		writeLogLine(newOutput.toString('utf8'));
	});

	// subProcess.stderr.on('data', (newOutput: Buffer) => {
	// 	console.error(newOutput.toString('utf8'));
	// });

	// subProcess.on('error', error => {

	// });

	const {waitUntilExit} = render(<App port={port} />, {
		exitOnCtrlC: true,
	});

	waitUntilExit().then(() => {
		console.log('Exiting...');
		subProcess.kill();
		process.exit(0);
	});
});
