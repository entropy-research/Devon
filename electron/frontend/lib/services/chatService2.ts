import axios from 'axios'
import { Chat } from '../chat.types'

const API_URL = 'http://127.0.0.1:8000' // URL where your FastAPI server is running

export async function createChat(chatData: Chat) {
    // try {
    //     const response = await axios.post(`${API_URL}/chats/`, chatData)
    //     return response.data
    // } catch (error) {
    //     console.error('Failed to create chat:', error)
    //     throw error
    // }
}

export async function getChat(chatId: string) {
    // try {
    //     const response = await axios.get(`${API_URL}/chats/${chatId}`)
    //     return response.data
    // } catch (error) {
    //     console.error('Failed to get chat:', error)
    // }
}

export async function updateChat(chatId: string, chatData: Chat) {
    // try {
    //     console.error('RAW', chatData)
    //     const response = await axios.patch(
    //         `${API_URL}/chats/${chatId}`,
    //         chatData
    //     )
    //     return response.data
    // } catch (error) {
    //     console.error('Failed to update chat:', error)
    //     throw error
    // }
}
