import { useEffect } from 'react'
import { Ellipsis, Trash } from 'lucide-react'
import { useReadSessions, useDeleteSession } from '@/lib/services/sessionService/sessionHooks'
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from '@/components/ui/popover'
import { useRouter, useSearchParams } from 'next/navigation'
import handleNavigate from './handleNavigate'

const SidebarChatLogs = () => {
    const { sessions, loading, error, refreshSessions } = useReadSessions()

    const { deleteSession } = useDeleteSession()
    const router = useRouter()
    const searchParams = useSearchParams()
    const sessionId = searchParams.get('chat')

    useEffect(() => {
        refreshSessions()
    }, [])

    // function clearChatAndRefresh() {
    //     clearChatData()
    //     location.reload()
    // }

    async function deleteChat(sessionId: string) {
        try {
            await deleteSession(sessionId) // Wait for the delete operation to complete
            await refreshSessions() // Then refresh the list of sessions
        } catch (error) {
            console.error('Failed to delete or refresh sessions:', error)
            // TODO: Optionally set an error state here and show it in the UI
        }
    }

    return (
        <div className="flex flex-col mt-2">
            {loading && <div className="px-2 py-2">Loading chats...</div>}
            {error && (
                <div className="px-2 py-2 text-red-400">
                    Error loading: {error}
                </div>
            )}
            {!loading &&
                sessions &&
                sessions.reverse().map((chatId: string, index: number) => (
                    <div
                        key={chatId}
                        className={`flex relative justify-between group items-center smooth-hover rounded-sm mx-2 ${chatId === sessionId ? 'bg-night border-l-2 border-primary' : ''}`}
                    >
                        <button
                            className="relative px-3 py-2 flex w-full items-center"
                            onClick={() => handleNavigate(chatId)}
                        >
                            <span className="text-ellipsis">
                                {chatId ? chatId : '(Unnamed chat)'}
                            </span>
                        </button>

                        <Popover>
                            <PopoverTrigger asChild>
                                <button className="opacity-0 group-hover:opacity-100 right-0 px-1 pl-1 pr-3 group-hover:hover-opacity">
                                    <Ellipsis size={24} className="pt-1" />
                                </button>
                            </PopoverTrigger>
                            <PopoverContent className="bg-night w-fit p-0">
                                <button
                                    onClick={() => deleteChat(chatId)}
                                    className="flex gap-2 justify-start items-center p-2 pr-3 text-sm"
                                >
                                    <Trash size={16} /> Delete session
                                </button>
                            </PopoverContent>
                        </Popover>
                    </div>
                ))}
        </div>
    )
}

export default SidebarChatLogs
