import { IDisposable, Terminal } from '@xterm/xterm'
import React, { useEffect, useRef } from 'react'
import '@xterm/xterm/css/xterm.css'

// import socket from "../socket/socket";

export default function ShellWidget() {
    return <Shell />
}

// Source: https://github.com/OpenDevin/OpenDevin/blob/main/frontend/src/components/Terminal.tsx
class JsonWebsocketAddon {
    _socket: WebSocket

    _disposables: IDisposable[]

    constructor(_socket: WebSocket) {
        this._socket = _socket
        this._disposables = []
    }

    activate(terminal: Terminal) {
        this._disposables.push(
            terminal.onData(data => {
                const payload = JSON.stringify({ action: 'terminal', data })
                this._socket.send(payload)
            })
        )
        this._socket.addEventListener('message', event => {
            const { action, args, observation, content } = JSON.parse(
                event.data
            )
            if (action === 'run') {
                terminal.writeln(args.command)
            }
            if (observation === 'run') {
                content.split('\n').forEach((line: string) => {
                    terminal.writeln(line)
                })
                terminal.write('\n$ ')
            }
        })
    }

    dispose() {
        this._disposables.forEach(d => d.dispose())
        this._socket.removeEventListener('message', () => {})
    }
}

/**
 * The terminal's content is set by write messages. To avoid complicated state logic,
 * we keep the terminal persistently open as a child of <App /> and hidden when not in use.
 */

function Shell(): JSX.Element {
    const terminalRef = useRef<HTMLDivElement>(null)
    const terminalInitialized = useRef(false) // Add this line

    useEffect(() => {
        if (terminalInitialized.current) return
        if (!terminalRef.current) return // Ensure the ref is current before proceeding

        const initTerminal = async () => {
            // console.log('init')
            // const { FitAddon } = await import('xterm-addon-fit')
            // const fitAddon = new FitAddon()
            // terminal.loadAddon(fitAddon)
            // Without this timeout, `fitAddon.fit()` throws the error
            // "this._renderer.value is undefined"
            // setTimeout(() => {
            //     fitAddon.fit()
            // }, 1)
            terminal.open(terminalRef.current as HTMLDivElement)
        }

        let terminal: Terminal
        terminal = new Terminal({
            // This value is set to the appropriate value by the
            // `fitAddon.fit()` call below.
            // If not set here, the terminal does not respect the width
            // of its parent element. This causes a bug where the terminal
            // is too large and switching tabs causes a layout shift.
            cols: 0,
            fontFamily: "Menlo, Monaco, 'Courier New', monospace",
            fontSize: 14,
            theme: {
                // background: bgColor,
            },
        })
        terminalInitialized.current = true
        terminal.write('$ ')

        initTerminal()

        // const bgColor = getComputedStyle(document.documentElement)
        //     .getPropertyValue('--bg-workspace')
        //     .trim()

        // const jsonWebsocketAddon = new JsonWebsocketAddon(socket);
        // terminal.loadAddon(jsonWebsocketAddon);

        return () => {
            terminal?.dispose()
            terminalInitialized.current = false // Reset on cleanup
        }
    }, [])

    return (
        <div className="flex flex-col h-full">
            <div className="text-sm px-4 py-2 text-lg border-b border-border">
                default
            </div>
            <div className="grow flex min-h-0 h-full">
                <div ref={terminalRef} className="h-full w-full rounded-lg" />
            </div>
        </div>
    )
}
