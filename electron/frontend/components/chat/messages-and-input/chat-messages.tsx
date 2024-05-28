import { ChatList2 } from '@/components/vercel-chat/chat-list'

const ChatMessages = ({ messages }) => {
    return messages?.length ? (
        <ChatList2
            messages={messages}
            isShared={false}
            // spinning={modelLoading}
        />
    ) : (
        <></>
    )
}

export default ChatMessages
