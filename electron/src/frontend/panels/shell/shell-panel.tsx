import { Terminal as XtermTerminal } from '@xterm/xterm'
import '@xterm/xterm/css/xterm.css'
import { useEffect, useRef, useState } from 'react'
import type { Message } from '@/lib/types'
import { parseCommand } from '@/lib/utils'

/**
 * The terminal's content is set by write messages. To avoid complicated state logic,
 * we keep the terminal persistently open as a child of <App /> and hidden when not in use.
 */

// TODO don't hardcode
const ignoreCommands = [
    'ask_user',
    'create_file',
    'open_file',
    'scroll_up',
    'scroll_down',
    'scroll_to_line',
    'search_file',
    'edit_file',
    'edit',
    'search_dir',
    'find_file',
    'get_cwd',
    'no_op',
    'submit',
    'delete_file',
    'code_search',
    'code_goto',
    'file_tree_display',
    'close_file',
    'exit',
    'extract_signature_and_docstring',
    'find_class',
    'find_function',
    'list_dirs_recursive',
    'parse_command',
    'real_write_diff',
]

export default function ShellPanel({
    messages,
    path,
}: {
    messages: Message[]
    path: string
}): JSX.Element {
    const terminalRef = useRef<HTMLDivElement>(null)
    const terminalInstanceRef = useRef<XtermTerminal | null>(null)
    const [renderedMessages, setRenderedMessages] = useState<Message[]>([])
    const initialPathRef = useRef<string | null>(null)

    useEffect(() => {
        // When the path changes, reset states
        if (
            initialPathRef.current === null ||
            path !== initialPathRef.current
        ) {
            setRenderedMessages([])
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
            const messagesToRender = messages.filter(message => {
                if (renderedMessages.includes(message)) return
                let [command, response] = message.text.split('|START_RESPONSE|')
                const parsedRes = parseCommand(command)

                if (parsedRes && ignoreCommands.includes(parsedRes?.command)) {
                    return
                }
                if (!parsedRes) {
                    return
                }
                return message
            })
            // terminal.clear() // Clear the existing content
            messagesToRender.forEach((message, idx) => {
                let [command, response] = message.text.split('|START_RESPONSE|')
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
                setRenderedMessages(prevMessages => [...prevMessages, message])
            })
        }
    }, [messages, renderedMessages])

    return (
        <div className="h-full flex flex-col bg-midnight">
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
