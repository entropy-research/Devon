'use server'
import { promises as fs } from 'fs'
import { join } from 'path'
import { Chat } from '../chat.types'

// Define the path to your JSON file
const FILE_PATH = join(__dirname, 'chatData.json')

// Function to load chat data from the file
export async function loadChatData(): Promise<Chat[]> {
    try {
        const data = await fs.readFile(FILE_PATH, 'utf8')
        return JSON.parse(data)
    } catch (error) {
        // If the file does not exist, return an empty array
        if (error.code === 'ENOENT') {
            return []
        } else {
            throw error
        }
    }
}

// Function to save chat data to the file
export async function saveChatData(chats: Chat[]): Promise<void> {
    try {
        const data = JSON.stringify(chats, null, 4)
        await fs.writeFile(FILE_PATH, data, 'utf8')
    } catch (error) {
        throw error
    }
}

// Function to clear chat data from the file
export async function clearChatData(): Promise<void> {
    try {
        await fs.writeFile(FILE_PATH, JSON.stringify([], null, 4), 'utf8')
        console.log('Chat data cleared successfully.')
    } catch (error) {
        console.error('Failed to clear chat data:', error)
        throw error
    }
}
