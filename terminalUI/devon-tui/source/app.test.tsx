import React from 'react';
import {render} from 'ink-testing-library';
import {App} from './app.js';

describe('App', () => {
	it('should render the App component', () => {
		const {lastFrame} = render(<App />);
		expect(lastFrame()).toMatchSnapshot();
	});
});
