import { Message } from 'ai'
import { Chat } from '@/lib/chat.types'
import { IpcMainInvokeEvent } from 'electron'

export async function getChatMessages() {
    const res = await window.api.invoke('get-messages')
    if (res.success) {
        return res.data
    }
}

export async function addChatMessage(message: Message) {
    const res = await window.api.invoke('add-message', message)
}

export async function createOrUpdateChat(chat: Chat) {
    const res = await window.api.invoke('create-or-update-chat', chat)
}

export async function getChats() {
    const res = await window.api.invoke('get-chats')
    if (res.success) {
        return res.data
    }
}

export async function createChat(chat: Chat) {
    const res = await window.api.invoke('create-chat', chat)
}

export async function getChatById(id: string) {
    const res = await window.api.invoke('get-chat-by-id', id)
    if (res.success) {
        return res.data
    }
}
