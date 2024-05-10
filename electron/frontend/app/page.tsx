'use client'
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
// import { useRouter } from 'next/router';
import { QueryClient, QueryClientProvider } from 'react-query'
import { useEffect } from 'react'
const queryClient = new QueryClient()

// export default async function IndexPage() {
//     // const router = useRouter();

//     const session = (await auth()) as Session
//     const missingKeys = await getMissingKeys()
//     const userId = session?.user?.id
//     // const chatId = nanoid()
//     const chatId = '1'
//     let chat: Chat = await loadChat(chatId)
//     // let chat: Chat | null = null
//     const initialized = false

//     async function loadChat(chatId) {
//         let _chat = await getChat(chatId)
//         if (!_chat) {
//             // Create a new chat if it does not exist
//             _chat = {
//                 id: chatId,
//                 title: 'title',
//                 createdAt: new Date(),
//                 userId: userId ?? '1',
//                 path: './',
//                 messages: [],
//                 // sharePath: 'sharePath',
//             }
//             createChat(_chat)
//         }
//         return _chat
//     }

//     const chatProps: ChatProps = {
//         id: chat?.id ?? '',
//         session: session,
//         missingKeys: missingKeys,
//     }

//     return (
//         <AI initialAIState={{ chatId: chat.id, messages: chat.messages }}>
//             <Landing chatProps={chatProps} />
//         </AI>
//     )
// }

export default function IndexPage() {
    // const router = useRouter();

    let session: Session | null = null
    let missingKeys: string[] = []
    let chat: Chat | null = null

    useEffect(() => {
        async function fetchData() {
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
                id: chat?.id ?? '',
                session: session,
                missingKeys: missingKeys,
            }
        }
        fetchData()
    }, [])

    const chatProps: ChatProps = {
        id: chat?.id ?? '',
        session: session,
        missingKeys: missingKeys,
    }

    return (
        <QueryClientProvider client={queryClient}>
            {/* <AI initialAIState={{ chatId: chat.id, messages: chat.messages }}> */}
            <Landing chatProps={chatProps} />
            {/* </AI> */}
        </QueryClientProvider>
    )
}
