import Database from 'better-sqlite3'
import path from 'path'
import { app } from 'electron'
import { Chat } from './types'

const dbPath = path.join(app.getPath('userData'), 'app-database.db')
const db = new Database(dbPath)

// db.exec(`
//   CREATE TABLE IF NOT EXISTS messages (
//     id TEXT PRIMARY KEY,
//     role TEXT,
//     content TEXT,
//     createdAt DATETIME DEFAULT CURRENT_TIMESTAMP
//   );
// `)

db.exec(`
    CREATE TABLE IF NOT EXISTS chats (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
        userId TEXT NOT NULL,
        path TEXT NOT NULL,
        messages TEXT,  -- This field will store the JSON array of messages
        sharePath TEXT
    );
`)

export const addMessage = (id: string, role: string, content: string) => {
  const stmt = db.prepare(
    'INSERT INTO messages (id, role, content) VALUES (?, ?, ?)'
  )
  stmt.run(id, role, content)
}

export const getMessages = () => {
  return db.prepare('SELECT * FROM messages ORDER BY createdAt DESC').all()
}

export const createChat = (chat: Chat): void => {
  try {
    const messagesJson = JSON.stringify(chat.messages) // Convert messages array to JSON string
    const stmt = db.prepare(`
        INSERT INTO chats (id, title, userId, path, messages, sharePath) 
        VALUES (?, ?, ?, ?, ?, ?);
      `)
    stmt.run(
      chat.id,
      chat.title,
      chat.userId,
      chat.path,
      messagesJson,
      chat.sharePath || null
    )
    console.log('Chat created successfully.')
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } catch (error: any) {
    if (error && error.code === 'SQLITE_CONSTRAINT_PRIMARYKEY') {
      console.error('A chat with the same ID already exists.')
    } else {
      console.error('Failed to create chat:', error)
    }
  }
}

export const createOrUpdateChat = (chat: Chat): void => {
  const messagesJson = JSON.stringify(chat.messages) // Convert messages array to JSON string
  const stmt = db.prepare(`
      INSERT INTO chats (id, title, userId, path, messages, sharePath) 
      VALUES (?, ?, ?, ?, ?, ?)
      ON CONFLICT(id) DO UPDATE SET
        title = excluded.title,
        userId = excluded.userId,
        path = excluded.path,
        messages = excluded.messages,
        sharePath = excluded.sharePath;
    `)
  stmt.run(
    chat.id,
    chat.title,
    chat.userId,
    chat.path,
    messagesJson,
    chat.sharePath || null
  )
}

export const getChats = (): Chat[] => {
  const stmt = db.prepare('SELECT * FROM chats ORDER BY createdAt DESC')
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const chats: Array<any> = stmt.all()
  return chats.map(chat => ({
    ...chat,
    messages: JSON.parse(chat.messages), // Parse the JSON string back to an array
  }))
}

export const getChatById = (id: string): Chat | null => {
  try {
    const stmt = db.prepare(`
        SELECT * FROM chats WHERE id = ?;
      `)

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const chat: any = stmt.get(id)

    if (chat) {
      return {
        ...chat,
        createdAt: new Date(chat.createdAt),
        messages: JSON.parse(chat.messages),
      } as Chat
    } else {
      console.log('No chat found with the specified ID.')
      return null
    }
  } catch (error) {
    console.error('Error retrieving chat by ID:', error)
    return null
  }
}
