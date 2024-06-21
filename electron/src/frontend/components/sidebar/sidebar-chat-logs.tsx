import { useEffect } from 'react'
import { Ellipsis, Trash } from 'lucide-react'
import {
    useReadSessions,
    useDeleteSession,
} from '@/lib/services/sessionService/sessionHooks'
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from '@/components/ui/popover'

const SidebarChatLogs = () => {
    const { sessions, loading, error, refreshSessions } = useReadSessions()

    const { deleteSession } = useDeleteSession()
    // const router = useRouter()
    // const searchParams = useSearchParams()
    const sessionId = 'UI'

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
                sessions
                    .reverse()
                    .map(
                        (
                            session: { name: string; path: string },
                            index: number
                        ) => (
                            <div
                                key={session.name}
                                className={`flex relative justify-between group items-center smooth-hover rounded-sm mx-2 ${
                                    session.name === sessionId
                                        ? 'bg-night border-l-2 border-primary'
                                        : ''
                                }`}
                            >
                                <button
                                    className="relative px-3 py-2 flex w-full items-center"
                                    onClick={() => handleNavigate(session.name)}
                                >
                                    <span className="text-ellipsis">
                                        {session.name
                                            ? session.name
                                            : '(Unnamed chat)'}
                                    </span>
                                </button>

                                <Popover>
                                    <PopoverTrigger asChild>
                                        <button className="opacity-0 group-hover:opacity-100 right-0 px-1 pl-1 pr-3 group-hover:hover-opacity">
                                            <Ellipsis
                                                size={24}
                                                className="pt-1"
                                            />
                                        </button>
                                    </PopoverTrigger>
                                    <PopoverContent className="bg-night w-fit p-0">
                                        <button
                                            onClick={() =>
                                                deleteChat(session.name)
                                            }
                                            className="flex gap-2 justify-start items-center p-2 pr-3 text-sm"
                                        >
                                            <Trash size={16} /> Delete session
                                        </button>
                                    </PopoverContent>
                                </Popover>
                            </div>
                        )
                    )}
        </div>
    )
}

function handleNavigate(sessionId: string, path?: string) {
    const currentUrl = window.location.href
    const pathname = window.location.pathname
    const searchParams = new URLSearchParams(window.location.search)

    // Encode the path

    // Set the search parameters
    searchParams.set('chat', sessionId)
    if (path) {
        searchParams.set('path', encodeURIComponent(path))
    }

    // Construct the new search string
    const newSearch = searchParams.toString()

    // Determine if the current URL is the root or specifically the chat query
    const isRootOrChat =
        pathname === '/' &&
        (!window.location.search ||
            window.location.search === `?chat=${sessionId}`)

    if (isRootOrChat) {
        // If we're already at the root and the session ID in the query matches or there's no query, just reload
        // window.location.reload()
    } else {
        // Otherwise, replace the state to include `?chat={sessionId}&path={encodedPath}` and reload
        window.history.replaceState({}, '', `/?${newSearch}`)
        // window.location.reload()
    }
}

export default SidebarChatLogs
