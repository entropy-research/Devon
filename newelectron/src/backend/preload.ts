// See the Electron documentation for details on how to use preload scripts:
// https://www.electronjs.org/docs/latest/tutorial/process-model#preload-scripts
/* eslint-disable @typescript-eslint/no-var-requires */
/* eslint-disable @typescript-eslint/no-explicit-any */

// Electron doesnt support ESM for renderer process. Alternatively, pass this file
// through a bundler but that feels like an overkill
const { contextBridge, ipcRenderer } = require('electron')

type Channel =
  | 'ping'
  | 'get-file-path'
  | 'file-path-response'
  | 'encrypt-data'
  | 'decrypt-data'
  | 'save-data'
  | 'load-data'
  | 'check-has-encrypted-data'
  | 'delete-encrypted-data'
  | 'server-port'
  | 'spawn-devon-agent'
  | 'get-port'
  | 'get-port-response'

const channels: { send: Channel[]; invoke: Channel[]; receive: Channel[] } = {
  send: ['get-file-path', 'ping', 'server-port', 'get-port'],
  invoke: [
    'ping',
    'get-file-path',
    'encrypt-data',
    'decrypt-data',
    'save-data',
    'load-data',
    'delete-encrypted-data',
    'check-has-encrypted-data',
    'spawn-devon-agent',
  ],
  receive: ['file-path-response', 'server-port', 'get-port-response'],
}

type ReceiveHandler = (event: any, ...arg: [any?, any?, any?]) => void

interface API {
  send: (channel: Channel, data: any) => void
  invoke: (channel: Channel, data: any) => Promise<any>
  receive: (channel: Channel, func: ReceiveHandler) => void
  removeAllListeners: (channel: Channel) => void
}

const api: API = {
  send: (channel, data) => {
    // Whitelist channels
    const validChannels: Channel[] = channels.send
    if (validChannels.includes(channel)) {
      ipcRenderer.send(channel, data)
    } else {
      throw new Error(`Invalid channel: ${channel}`)
    }
  },
  invoke: (channel, data) => {
    // Whitelist channels
    const validChannels: Channel[] = channels.invoke
    if (validChannels.includes(channel)) {
      return ipcRenderer.invoke(channel, data)
    } else {
      throw new Error(`Invalid channel: ${channel}`)
    }
  },
  receive: (channel, func) => {
    const validChannels: Channel[] = channels.receive
    if (validChannels.includes(channel)) {
      // Deliberately strip event as it includes `sender`
      ipcRenderer.on(channel, (event: any, ...args: [any?, any?, any?]) =>
        func(...args)
      )
    } else {
      throw new Error(`Invalid channel: ${channel}`)
    }
  },
  removeAllListeners: channel => {
    ipcRenderer.removeAllListeners(channel)
  },
}

contextBridge.exposeInMainWorld('api', api)
