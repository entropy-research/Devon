'use client'
import { List, Settings } from 'lucide-react'
import { useContext, createContext, useState, useRef } from 'react'
import SidebarHeader from './sidebar-header'
import SidebarChatLogs from './sidebar-chat-logs'
import SidebarItem from './sidebar-item'

const defaultValue = {
    expanded: true,
}

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

const bottomSidebarItems = [
    {
        icon: <Settings className="text-primary" />,
        text: 'Settings',
        active: true,
        alert: false,
        route: '/settings',
    },
]

const SidebarContext = createContext(defaultValue)

export default function Sidebar() {
    const [expanded, setExpanded] = useState(false)
    const timerRef = useRef<NodeJS.Timeout | null>(null)
    // const { expanded } = useContext(SidebarContext)

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
                        {bottomSidebarItems.map(item => (
                            <SidebarItem
                                key={item.text}
                                {...item}
                                expanded={expanded}
                            />
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
