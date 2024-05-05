// For Chat
'use server'

import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'
import { kv } from '@vercel/kv'

import { auth } from '@/chat.auth'
import { type Chat } from '@/lib/chat.types'
import { Message } from 'ai'
// import { sendMessage, loadMessages } from '@/lib/services/electronServices'
// import { readChats, writeChats } from '@/lib/services/chatStorage'
// import { fetchUserDataPath } from '@/lib/services/electronServices'
import { loadChatData, saveChatData } from '@/lib/services/chatDataService'
import { createOrUpdateChat, getChatById } from '@/lib/services/chatService'

// Not used
export async function getChats(userId?: string | null) {
    if (!userId) {
        return []
    }

    try {
        const pipeline = kv.pipeline()
        const chats: string[] = await kv.zrange(`user:chat:${userId}`, 0, -1, {
            rev: true,
        })

        for (const chat of chats) {
            pipeline.hgetall(chat)
        }

        const results = await pipeline.exec()

        return results as Chat[]
    } catch (error) {
        return []
    }
}

// export async function getChat(id: string, userId: string) {
//     const chat: Chat = await getChatById(id)
//     if (!chat) {
//         return null
//     }
//     return chat
// }

export async function getChat2(id: string, userId: string) {
    //   const chat = await kv.hgetall<Chat>(`chat:${id}`)

    // const messages = await loadMessages()
    // const chats = await readChats()
    const chats: Chat[] = await loadChatData()
    // console.log('CHATS', chats)
    // const messages = []
    // const path = await fetchUserDataPath()
    // console.log('path', path)

    const chat = chats.find(c => c.id === id)

    if (!chat) {
        // Create a new chat if it does not exist
        return {
            id,
            title: 'title',
            createdAt: new Date(),
            userId,
            path: './',
            messages: [],
            sharePath: 'sharePath',
        }
    }

    if (!chat || (userId && chat.userId !== userId)) {
        return null
    }

    return chat
}

export async function removeChat({ id, path }: { id: string; path: string }) {
    const session = await auth()

    if (!session) {
        return {
            error: 'Unauthorized',
        }
    }

    //Convert uid to string for consistent comparison with session.user.id
    const uid = String(await kv.hget(`chat:${id}`, 'userId'))

    if (uid !== session?.user?.id) {
        return {
            error: 'Unauthorized',
        }
    }

    await kv.del(`chat:${id}`)
    await kv.zrem(`user:chat:${session.user.id}`, `chat:${id}`)

    revalidatePath('/')
    return revalidatePath(path)
}

export async function clearChats() {
    const session = await auth()

    if (!session?.user?.id) {
        return {
            error: 'Unauthorized',
        }
    }

    const chats: string[] = await kv.zrange(
        `user:chat:${session.user.id}`,
        0,
        -1
    )
    if (!chats.length) {
        return redirect('/')
    }
    const pipeline = kv.pipeline()

    for (const chat of chats) {
        pipeline.del(chat)
        pipeline.zrem(`user:chat:${session.user.id}`, chat)
    }

    await pipeline.exec()

    revalidatePath('/')
    return redirect('/')
}

export async function getSharedChat(id: string) {
    const chat = await kv.hgetall<Chat>(`chat:${id}`)

    if (!chat || !chat.sharePath) {
        return null
    }

    return chat
}

export async function shareChat(id: string) {
    const session = await auth()

    if (!session?.user?.id) {
        return {
            error: 'Unauthorized',
        }
    }

    const chat = await kv.hgetall<Chat>(`chat:${id}`)

    if (!chat || chat.userId !== session.user.id) {
        return {
            error: 'Something went wrong',
        }
    }

    const payload = {
        ...chat,
        sharePath: `/share/${chat.id}`,
    }

    await kv.hmset(`chat:${chat.id}`, payload)

    return payload
}

// export async function saveChat(chat: Chat) {
//     const session = await auth()

//     if (session && session.user) {
//         const pipeline = kv.pipeline()
//         pipeline.hmset(`chat:${chat.id}`, chat)
//         pipeline.zadd(`user:chat:${chat.userId}`, {
//             score: Date.now(),
//             member: `chat:${chat.id}`,
//         })
//         await pipeline.exec()
//     } else {
//         return
//     }
// }
import { updateChat } from '@/lib/services/chatService2'

export async function saveChat(chat: Chat) {
    // await createOrUpdateChat(chat)
    const chats: Chat[] = await loadChatData()
    const existingChat = chats.find(c => c.id === chat.id)

    if (existingChat) {
        const index = chats.indexOf(existingChat)
        chats[index] = chat
    } else {
        chats.push(chat)
    }
    updateChat(chat.id, chat)
    saveChatData(chats)

    return chats
}

export async function refreshHistory(path: string) {
    redirect(path)
}

export async function getMissingKeys() {
    const keysRequired = ['OPENAI_API_KEY']
    return keysRequired
        .map(key => (process.env[key] ? '' : key))
        .filter(key => key !== '')
}
