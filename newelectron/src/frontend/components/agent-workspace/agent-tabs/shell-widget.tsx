import { Terminal as XtermTerminal } from '@xterm/xterm'
import '@xterm/xterm/css/xterm.css'
import { useEffect, useRef, useState } from 'react'

import type { Message } from '@/lib/services/stateMachineService/stateMachine'

/**
 * The terminal's content is set by write messages. To avoid complicated state logic,
 * we keep the terminal persistently open as a child of <App /> and hidden when not in use.
 */

export default function ShellWidget({
    messages,
}: {
    messages: Message[]
}): JSX.Element {
    const terminalRef = useRef<HTMLDivElement>(null)
    const terminalInstanceRef = useRef<XtermTerminal | null>(null)
    const [renderedMessages, setRenderedMessages] = useState<Message[]>([])

    useEffect(() => {
        async function addOn() {
            const { FitAddon } = await import('@xterm/addon-fit')
            const fitAddon = new FitAddon()
            terminal.loadAddon(fitAddon)
            // Without this timeout, `fitAddon.fit()` throws the error
            // "this._renderer.value is undefined"
            setTimeout(() => {
                fitAddon.fit()
            }, 1)
        }

        const bgColor = getComputedStyle(document.documentElement)
            .getPropertyValue('--bg-workspace')
            .trim()
        const terminal = new XtermTerminal({
            // This value is set to the appropriate value by the
            // `fitAddon.fit()` call below.
            // If not set here, the terminal does not respect the width
            // of its parent element. This causes a bug where the terminal
            // is too large and switching tabs causes a layout shift.
            cols: 0,
            fontFamily: "Menlo, Monaco, 'Courier New', monospace",
            fontSize: 11,
            theme: {
                background: '#111111',
            },
            cursorBlink: true,
        })

        terminal.open(terminalRef.current as HTMLDivElement)
        terminalInstanceRef.current = terminal // Store the terminal instance
        terminal.write('> ')

        addOn()

        return () => {
            terminal.dispose()
            terminalInstanceRef.current = null
        }
    }, [])

    useEffect(() => {
        const terminal = terminalInstanceRef.current
        if (terminal) {
            const messagesToRender = messages.filter(message => !renderedMessages.includes(message))
            // terminal.clear() // Clear the existing content
            messagesToRender.forEach((message, idx) => {
                let [command, response] = message.text.split('|START_RESPONSE|')
                let commandMsgs = command.slice(18).trim().split('\n')
                commandMsgs.forEach((line, index) => {
                    if (index === 0) {
                        const firstLineItems = line.trim().split(' ')
                        let end: string | undefined = undefined

                        // Check if the last item in the first line is "<<<"
                        if (
                            firstLineItems[firstLineItems.length - 1] === '<<<'
                        ) {
                            end = firstLineItems.pop() // Remove the "<<<"
                        }

                        // Construct the command string
                        line = 'bash>  ' + firstLineItems.join(' ')
                        if (end) {
                            terminal.writeln(line)
                            terminal.writeln(end)
                            return
                        }
                    }
                    terminal.writeln(line)
                })
                if (response) {
                    let responseMsgs = response.trim().split('\n')
                    responseMsgs.forEach(line => {
                        terminal.writeln(line)
                    })
                }
                setRenderedMessages(prevMessages => [...prevMessages, message])
            })
        }
    }, [messages, renderedMessages])

    return (
        <div className="h-full flex flex-col bg-midnight">
            <div
                id="terminal-wrapper"
                className="flex-grow flex bg-midnight w-full pl-3 pr-[1px] pt-3 overflow-hidden border-t border-outlinecolor"
            >
                <div
                    id="terminal-ref"
                    ref={terminalRef}
                    className="w-full overflow-auto"
                />
            </div>
        </div>
    )
}
