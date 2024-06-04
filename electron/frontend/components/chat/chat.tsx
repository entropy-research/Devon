import ChatHeader from './chat-header'
import ChatMessagesAndInput from '@/components/chat/chat-messages-and-input/chat-messages-and-input'
import { theme } from '@/lib/config'

export default function Chat({
    sessionId,
    viewOnly = false,
    headerIcon,
    loading = false,
}: {
    sessionId: string | null
    viewOnly?: boolean
    headerIcon?: JSX.Element
    loading?: boolean
}) {
    return (
        <div
            className={`rounded-lg h-full w-full max-w-4xl flex flex-col flex-2 ${theme.showChatBorders.enabled ? 'border border-outlinecolor ml-3 rounded-md' : ''} ${theme.showChatBorders.enabled && theme.showChatBorders.darkChat ? 'bg-fade-bottom-to-top-midnight' : ''}`}
        >
            <ChatHeader sessionId={sessionId} headerIcon={headerIcon} />

            <ChatMessagesAndInput
                viewOnly={viewOnly}
                loading={loading}
                sessionId={sessionId as string}
            />
        </div>
    )
}
