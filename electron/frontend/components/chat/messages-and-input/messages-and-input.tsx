import { ChatProps } from '@/lib/chat.types'
import { VercelChat } from '@/components/chat/messages-and-input/vercel.chat'

export default function MessagesAndInput({
    viewOnly,
    chatProps,
}: {
    viewOnly: boolean
    chatProps?: ChatProps
}) {
    return (
        // <div className="flex flex-1 overflow-y-scroll flex-col">
        <VercelChat viewOnly={viewOnly} {...chatProps} />
        // </div>
    )
}
