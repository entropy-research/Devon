/* eslint-disable @typescript-eslint/no-var-requires */
/* eslint-disable @typescript-eslint/no-explicit-any */

// Electron doesnt support ESM for renderer process. Alternatively, pass this file
// through a bundler but that feels like an overkill
const { contextBridge, ipcRenderer } = require('electron')

type Channel =
  | 'get-file-path'
  | 'add-message'
  | 'get-messages'
  | 'ping'
  | 'get-conversation-history'
  | 'file-path-response'
  | 'create-chat'
  | 'create-or-update-chat'
  | 'get-chats'
  | 'get-chat-by-id'
  | 'encrypt-data'
  | 'decrypt-data'
  | 'save-data'
  | 'load-data'
  | 'delete-encrypted-data'
  | 'check-has-encrypted-data'
  | 'server-port'

const channels: { send: Channel[]; invoke: Channel[]; receive: Channel[] } = {
  send: ['get-file-path', 'add-message', 'ping', 'server-port'],
  invoke: [
    'get-file-path',
    'add-message',
    'get-messages',
    'ping',
    'get-conversation-history',
    'create-chat',
    'create-or-update-chat',
    'get-chats',
    'get-chat-by-id',
    'encrypt-data',
    'decrypt-data',
    'save-data',
    'load-data',
    'delete-encrypted-data',
    'check-has-encrypted-data',
  ],
  receive: ['file-path-response', 'server-port'],
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
