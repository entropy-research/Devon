import { Power } from 'lucide-react'
export default function ChatHeader({
    sessionId,
    headerIcon,
}: {
    sessionId?: string | null
    headerIcon?: JSX.Element
}) {
    // if (!sessionId || sessionId === 'New') {
    //     return <></>
    // }
    return (
        <div className="relative mt-4 items-end pt-1 pb-3 border-outline-night shrink-0 items-left flex flex-row justify-between border-b px-8">
            {/* <div className="">
                <p className="text-lg mb-2">Hey there!</p>
                <p className="text-gray-400 text-sm">{`My name is Devon and I'm a software engineer. Give me coding tasks and I will try my best to solve them!`}</p>
            </div> */}
            <p className="text-lg font-semibold pb-[1px]">Create a snake game</p>
            <button className="flex items-center gap-2 smooth-transition hover:border-gray-400 hover:bg-batman transition duration-300 px-3 py-1 -mr-3 rounded-lg group">
                {/* group-hover:text-red-500 */}
                <Power size={14} className="group-hover:transition text-gray-400 group-hover:text-white duration-300 mb-[1px]"/>
                <p className="group-hover:transition duration-300 text-gray-400 group-hover:text-white">End session</p>
            </button>

            {headerIcon}
        </div>
    )
}
