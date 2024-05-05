export interface Message {
  id: string
  role: string
  content: string
}

export interface StoreSchema {
  conversationHistory: Message[]
}

/* eslint-disable @typescript-eslint/no-explicit-any */
export interface Chat extends Record<string, any> {
  id: string
  title: string
  createdAt: Date
  userId: string
  path: string
  messages: Message[]
  sharePath?: string
}
