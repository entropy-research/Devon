import { Terminal as XtermTerminal } from '@xterm/xterm'
import '@xterm/xterm/css/xterm.css'
import { useEffect, useMemo, useRef, useState } from 'react'
import type { Message } from '@/lib/types'
import { parseCommand } from '@/lib/utils'
import { SessionMachineContext } from '@/contexts/session-machine-context'
import { shallowEqual } from '@xstate/react'
import { computeNewLineNumber } from 'react-diff-view'

/**
 * The terminal's content is set by write messages. To avoid complicated state logic,
 * we keep the terminal persistently open as a child of <App /> and hidden when not in use.
 */


type ShellCommand = {
    command: string
    response: string
}

export default function ShellPanel({
    path,
}: {
    // messages: Message[]
    path: string
}): JSX.Element {
    const terminalRef = useRef<HTMLDivElement>(null)
    const terminalInstanceRef = useRef<XtermTerminal | null>(null)
    // const [renderedMessages, setRenderedMessages] = useState<ShellCommand[]>([])
    let renderedMessages: ShellCommand[] = []
    const initialPathRef = useRef<string | null>(null)
    const messages = SessionMachineContext.useSelector(state =>
        state.context.serverEventContext.messages.filter(
            message => message.type === 'shellCommand' || message.type === 'shellResponse'
        ),
        shallowEqual
    )
    useEffect(() => {
        // When the path changes, reset states
        if (
            initialPathRef.current === null ||
            path !== initialPathRef.current
        ) {
            renderedMessages = []
            if (terminalInstanceRef.current) {
                terminalInstanceRef.current.clear()
            }
            initialPathRef.current = path
        }
    }, [path])

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

    function removeBeforeRunningCommand(input: string): string {
        const regex = /.*Running Command:\s*/i
        return input.replace(regex, '')
    }

    useEffect(() => {
        const terminal = terminalInstanceRef.current
        if (terminal) {
            const messagesToRender = messages.reduce((acc, message) => {
                if (message.type === 'shellCommand') {
                    acc.push({ command: message.text, response: '' });
                } else if (acc.length > 0) {
                    acc[acc.length - 1].response += message.text;
                }
                return acc;
            }, [] as ShellCommand[])
            console.log(messagesToRender, renderedMessages)
            terminal.clear()
            // terminal.clear() // Clear the existing content
            messagesToRender.forEach((message, idx) => {
                console.log(message)
                const {command, response} = message
                // console.log("pusing", command, response)
                renderedMessages.push({ command, response })
                // console.log("after push",renderedMessages)

                let commandMsgs = removeBeforeRunningCommand(
                    command.trim()
                ).split('\n')
                commandMsgs.forEach((line, index) => {
                    terminal.writeln(line)
                })
                if (response) {
                    let responseMsgs = response.trim().split('\n')
                    responseMsgs.forEach(line => {
                        terminal.writeln(line)
                    })
                    terminal.write('> ')
                }
            })
        }
    }, [messages])

    return (
        <div className="h-full flex flex-col bg-midnight toned-text-color leading-relaxed">
            <div
                id="terminal-wrapper"
                className="flex-grow flex bg-midnight w-full px-3 pr-[1px] pt-4 overflow-hidden border-t border-outlinecolor"
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
