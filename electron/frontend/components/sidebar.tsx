'use client'
import { List, Settings, Bot, SquarePen, Trash } from 'lucide-react'
import { useContext, createContext, useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import { clearChatData } from '../lib/services/chatDataService'

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

    function clearChatAndRefresh() {
        clearChatData()
        location.reload()
    }

    return (
        <aside className="h-full flex flex-row">
            <nav
                className="h-full flex flex-col bg-shade rounded-lg py-6"
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
                            {expanded && (
                                <button
                                    onClick={clearChatAndRefresh}
                                    className="flex p-3 gap-3 justify-center items-center"
                                >
                                    <Trash size={16} /> Clear current chat
                                </button>
                            )}
                            {expanded && <ChatLogs />}
                        </div>
                        <div>
                            {sidebarItems.map(item => (
                                <SidebarItem key={item.text} {...item} />
                            ))}
                        </div>
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
            {expanded && (
                <button>
                    <SquarePen size={20} className="text-primary" />
                </button>
            )}
        </div>
    )
}

export function SidebarItem({
    icon,
    text,
    active,
    alert,
}: {
    icon: JSX.Element
    text: string
    active: boolean
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
            <Link href="/settings" className="flex">
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

            {!expanded && (
                <div
                    className={`
          absolute left-full rounded-md px-2 py-1 ml-6
          bg-night text-sm
          invisible opacity-20 -translate-x-3 transition-all
          group-hover:visible group-hover:opacity-100 group-hover:translate-x-0
          z-10
          border border-outline-night
      `}
                >
                    {text}
                </div>
            )}
        </div>
    )
}

const ChatLogs = () => {
    return (
        <div>
            {expandedChatTabs.map(item => (
                <a key={item.text} href={item.route}>
                    {item.text}
                </a>
            ))}
        </div>
    )
}
