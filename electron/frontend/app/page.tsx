import { nanoid } from '@/lib/chat.utils'
import { AI } from '@/lib/chat/chat.actions'
import { auth } from '@/chat.auth'
import { Session } from '@/lib/chat.types'
import { getMissingKeys } from '@/app/chat.actions'
import { ChatProps } from '@/lib/chat.types'
// import { getChat } from '@/app/chat.actions'
import { getChatById } from '@/lib/services/chatService'
import { Chat } from '@/lib/chat.types'
import Home from './home'
import Landing from './landing'
import { getChat, createChat } from '@/lib/services/chatService2'

export default async function IndexPage() {
    const session = (await auth()) as Session
    const missingKeys = await getMissingKeys()
    const userId = session?.user?.id
    // const chatId = nanoid()
    const chatId = '1'
    let chat: Chat = await loadChat(chatId)
    // let chat: Chat | null = null
    const initialized = false

    async function loadChat(chatId) {
        let _chat = await getChat(chatId)
        if (!_chat) {
            // Create a new chat if it does not exist
            _chat = {
                id: chatId,
                title: 'title',
                createdAt: new Date(),
                userId: userId ?? '1',
                path: './',
                messages: [],
                // sharePath: 'sharePath',
            }
            createChat(_chat)
        }
        return _chat
    }

    const chatProps: ChatProps = {
        id: chat.id,
        session: session,
        missingKeys: missingKeys,
    }

    return (
        <AI initialAIState={{ chatId: chat.id, messages: chat.messages }}>
            <Landing chatProps={chatProps} />
        </AI>
    )
}
// import React, { useState, useEffect } from 'react'
// import { auth } from '@/chat.auth'
// import { getMissingKeys } from '@/app/chat.actions'
// import { getChatById } from '@/lib/services/chatService'
// import { AI } from '@/lib/chat/chat.actions'
// import Home from './home'
// import Landing from './landing'

// const IndexPage = () => {
//     const [session, setSession] = useState<Session>({
//         user: { id: '1' },
//     })
//     const [chat, setChat] = useState<Chat>()
//     const [initialized, setInitialized] = useState(false)

//     useEffect(() => {
//         const fetchData = async () => {
//             const sessionData = await auth()
//             setSession(sessionData)
//             const missingKeysData = await getMissingKeys()
//             const userId = sessionData?.user?.id
//             const chatId = '1'
//             let chatData = await getChatById(chatId)
//             if (!chatData) {
//                 // Simulate creating a new chat
//                 chatData = {
//                     id: chatId,
//                     title: 'New Chat',
//                     createdAt: new Date(),
//                     userId: userId,
//                     path: './',
//                     messages: [],
//                 }
//             }
//             setChat(chatData)
//             setInitialized(true)
//         }

//         fetchData()
//     }, [])

//     if (!initialized) return <Landing />

//     const chatProps: ChatProps = {
//         id: chat?.id,
//         session: session,
//         missingKeys: [],
//     }

//     return (
//         <AI
//             initialAIState={{
//                 chatId: chat?.id ?? '',
//                 messages: chat?.messages ?? [],
//             }}
//         >
//             <Home chatProps={chatProps} />
//         </AI>
//     )
// }

// export default IndexPage
