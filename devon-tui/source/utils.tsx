import fs from 'fs';

const LOG_FILE = './devon-tui.log';

const fd = fs.openSync(LOG_FILE, 'a');

export const writeLogLine = (line: string) => {
	try {
		fs.appendFileSync(fd, line + '\n');
	} catch (error) {}
};
