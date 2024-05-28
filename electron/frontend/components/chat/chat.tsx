import Header from './header'
import { SimpleChat } from '@/components/chat/messages-and-input/simple.chat'

export default function Chat({
    sessionId,
    viewOnly = false,
    headerIcon,
}: {
    sessionId: string | null
    viewOnly?: boolean
    headerIcon?: JSX.Element
}) {
    return (
        <div className="rounded-lg h-full w-full max-w-4xl flex flex-col flex-2">
            <Header sessionId={sessionId} headerIcon={headerIcon} />
            <div className="flex-1 overflow-y-auto">
                <SimpleChat viewOnly={viewOnly} />
            </div>
        </div>
    )
}
