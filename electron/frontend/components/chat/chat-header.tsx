import { SessionMachineContext } from '@/app/home'
import { CircleArrowDown, Power, Rewind, History } from 'lucide-react'
import { theme } from '@/lib/config'

export default function ChatHeader({
    sessionId,
    headerIcon,
}: {
    sessionId?: string | null
    headerIcon?: JSX.Element
}) {
    const host = SessionMachineContext.useSelector(state => state.context.host)
    const sessionActorRef = SessionMachineContext.useActorRef()

    async function handleReset() {
        sessionActorRef.send({ type: 'session.reset' })
    }

    async function handleStop() {
        sessionActorRef.send({ type: 'session.pause' })
    }

    return (
        <div
            className={`relative ${theme.showChatBorders.enabled ? 'mt-1' : 'mt-4'} items-end pt-1 pb-3 border-outline-night shrink-0 items-left flex flex-row justify-between border-b px-6`}
        >
            <p className="text-lg font-semibold pb-[1px]">Chat</p>
            <div className="flex gap-3 -mr-2">
                <RestartButton resetHandler={handleReset} />
                <StopButton stopHandler={handleStop} />
            </div>
            {headerIcon}
        </div>
    )
}

const RestartButton = ({ resetHandler }) => {
    return (
        <button
            onClick={resetHandler}
            className="group flex items-center gap-2 px-3 py-1 rounded-md mb-[-4px] -mr-2 smooth-hover"
        >
            <History
                size={14}
                className="group-hover:transition text-gray-400 duration-300 mb-[1px] group-hover:text-white"
            />
            <p className="group-hover:transition duration-300 text-gray-400 group-hover:text-white">
                Reset session
            </p>
        </button>
    )
}

const StopButton = ({ stopHandler }) => {
    return (
        <button
            onClick={stopHandler}
            className="group flex items-center gap-2 px-3 py-1 rounded-md mb-[-4px] smooth-hover"
        >
            <Power
                size={14}
                className="group-hover:transition text-gray-400 group-hover:text-white duration-300 mb-[1px]"
            />
            <p className="group-hover:transition duration-300 text-gray-400 group-hover:text-white">
                Stop session
            </p>
        </button>
    )
}
