import { ChatProps } from '@/lib/chat.types'
import Header from './header'
// import { VercelChat } from '@/components/chat/messages-and-input/vercel.chat'
import { SimpleChat } from '@/components/chat/messages-and-input/simple.chat'

export default function Chat({
    viewOnly = false,
    chatProps,
    headerIcon,
}: {
    viewOnly?: boolean
    chatProps?: ChatProps
    headerIcon?: JSX.Element
}) {
    return (
        <div className="rounded-lg h-full w-full max-w-4xl flex flex-col flex-2">
            <Header sessionId={chatProps?.id} headerIcon={headerIcon} />
            <div className="flex-1 overflow-y-auto">
                {/* <VercelChat viewOnly={viewOnly} {...chatProps} /> */}
                <SimpleChat viewOnly={viewOnly} {...chatProps} />
            </div>
        </div>
    )
}
