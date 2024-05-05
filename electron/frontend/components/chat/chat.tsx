import { ChatProps } from '@/lib/chat.types'
import Header from './header'
import MessagesAndInput from './messages-and-input/messages-and-input'

export default function Chat({
    viewOnly = false,
    chatProps,
}: {
    viewOnly?: boolean
    chatProps?: ChatProps
}) {
    return (
        <div className="dark:bg-shade rounded-lg h-full w-full flex flex-col flex-1">
            <Header />
            <div className="flex-1 overflow-y-auto">
                <MessagesAndInput viewOnly={viewOnly} chatProps={chatProps} />
            </div>
        </div>
    )
}
