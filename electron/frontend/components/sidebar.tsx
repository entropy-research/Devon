'use client'
import { List, Settings, Bot, SquarePen, Trash } from 'lucide-react'
import { useContext, createContext, useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import { Ellipsis } from 'lucide-react'
import { clearChatData } from '../lib/services/chatDataService'
import useReadSessions from '@/lib/services/sessionService/use-read-sessions'
import useDeleteSession from '@/lib/services/sessionService/use-delete-session'
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from '@/components/ui/popover'
import SelectProjectDirectoryModal from '@/components/modals/select-project-directory-modal'
// import { session } from 'electron'

const defaultValue = {
    expanded: true,
}

const SidebarContext = createContext(defaultValue)

const expandedChatTabs: {
    icon: JSX.Element
    text: string
    active: boolean
    alert: boolean
    route: string
    id: string
}[] = [
    // {
    //     icon: <List className="text-primary" />,
    //     text: 'New chat',
    //     active: true,
    //     alert: false,
    //     route: '/chat',
    //     id: '1',
    // },
]

const sidebarItems = [
    {
        icon: <Settings className="text-primary" />,
        text: 'Settings',
        active: true,
        alert: false,
        route: '/settings',
    },
]

export default function Sidebar() {
    const [expanded, setExpanded] = useState(false)
    const timerRef = useRef<NodeJS.Timeout | null>(null)

    function handleMouseOver() {
        if (timerRef.current) {
            clearTimeout(timerRef.current)
        }
        timerRef.current = setTimeout(() => {
            setExpanded(true)
        }, 300)
    }

    function handleMouseOut() {
        if (timerRef.current) {
            clearTimeout(timerRef.current)
        }
        timerRef.current = setTimeout(() => {
            setExpanded(false)
        }, 300)
    }

    return (
        <aside className="h-full flex flex-row">
            <nav
                className="h-full flex flex-col bg-shade rounded-lg py-6 max-w-[280px] w-full"
                onMouseOver={handleMouseOver}
                onMouseOut={handleMouseOut}
            >
                <SidebarContext.Provider value={{ expanded }}>
                    <ul
                        className={`flex-1 flex flex-col justify-between ${expanded ? 'px-3' : 'px-2 items-center'}`}
                    >
                        <div>
                            <SidebarHeader expanded={expanded} />
                            {!expanded && (
                                <button
                                    onClick={() => setExpanded(curr => !curr)}
                                    className="mt-3"
                                >
                                    <List className="text-primary" />
                                </button>
                            )}
                            {expanded && <SidebarChatLogs />}
                        </div>
                        {sidebarItems.map(item => (
                            <SidebarItem key={item.text} {...item} />
                        ))}
                    </ul>
                </SidebarContext.Provider>
            </nav>
            <div className="flex justify-center">
                <button onClick={() => setExpanded(curr => !curr)}>
                    <div className="flex h-8 w-6 flex-col items-center group">
                        <div
                            className={`h-4 w-1 rounded-full bg-gray-400 translate-y-0.5 rotate-0 ${expanded ? 'group-hover:rotate-[15deg]' : 'group-hover:rotate-[-15deg]'}`}
                        ></div>
                        <div
                            className={`h-4 w-1 rounded-full bg-gray-400 -translate-y-0.5 rotate-0 ${expanded ? 'group-hover:-rotate-[15deg]' : 'group-hover:rotate-[15deg]'}`}
                        ></div>
                    </div>
                </button>
            </div>
        </aside>
    )
}

const SidebarHeader = ({ expanded }: { expanded: boolean }) => {
    return (
        <div
            className={`flex flex-row ${expanded && 'border-b border-outline-day dark:border-outline-night mx-2'} pb-4 items-center justify-between`}
        >
            <Link href="/" className="flex">
                <Bot className="text-primary" />
                {expanded && (
                    <h1 className="text-lg font-semibold mx-3">Devon</h1>
                )}
            </Link>
            <SelectProjectDirectoryModal
                trigger={
                    <button className={expanded ? 'visible' : 'hidden'}>
                        <SquarePen size={20} className="text-primary" />
                    </button>
                }
            />
        </div>
    )
}

const SidebarChatLogs = () => {
    const { sessions, loading, error, refreshSessions } = useReadSessions()
    const { deleteSession } = useDeleteSession()

    useEffect(() => {
        refreshSessions()
    }, [])

    // function clearChatAndRefresh() {
    //     clearChatData()
    //     location.reload()
    // }

    async function deleteChat(sessionId: string) {
        try {
            await deleteSession(sessionId);  // Wait for the delete operation to complete
            await refreshSessions();  // Then refresh the list of sessions
        } catch (error) {
            console.error('Failed to delete or refresh sessions:', error);
            // TODO: Optionally set an error state here and show it in the UI
        }
    }

    return (
        <div className="flex flex-col mt-2">
            {loading && <div className="px-2 py-2">Loading sessions...</div>}
            {error && (
                <div className="px-2 py-2 text-red-400">
                    Error loading: {error}
                </div>
            )}
            {!loading &&
                sessions &&
                sessions.map((session: string, index: number) => (
                    <div
                        key={index}
                        className="flex relative justify-between w-full group items-center smooth-hover rounded-md"
                    >
                        <button className="relative px-4 py-3 flex w-full">
                            <span className="text-ellipsis">
                                {session ? session : '(Unnamed chat)'}
                            </span>
                        </button>

                        <Popover>
                            <PopoverTrigger asChild>
                                <button className="opacity-0 group-hover:opacity-100 right-0 px-1 pl-1 pr-3 group-hover:hover-opacity">
                                    <Ellipsis size={24} className="pt-1" />
                                </button>
                            </PopoverTrigger>
                            <PopoverContent className="bg-night w-fit min-w-[180px]">
                                <button
                                    onClick={() => deleteChat(session)}
                                    className="flex gap-2 justify-center items-center px-1"
                                >
                                    <Trash size={16} /> Delete chat
                                </button>
                            </PopoverContent>
                        </Popover>
                    </div>
                ))}
        </div>
    )
}

function SidebarItem({
    icon,
    text,
    active,
    route,
    alert,
}: {
    icon: JSX.Element
    text: string
    active: boolean
    route: string
    alert: boolean
}) {
    const { expanded } = useContext(SidebarContext)

    return (
        <div
            className={`
        relative flex py-2 px-3 my-1
        font-medium rounded-md cursor-pointer
        transition-colors group
    `}
        >
            <Link href={route} className="flex">
                {icon}
                <span
                    className={`overflow-hidden transition-all flex items-start ${
                        expanded ? 'w-52 ml-3' : 'w-0'
                    }`}
                >
                    {text}
                </span>
            </Link>
            {alert && (
                <div
                    className={`absolute right-2 w-2 h-2 rounded bg-primary ${
                        expanded ? '' : 'top-2'
                    }`}
                />
            )}
        </div>
    )
}
