'use client'
import { List, Settings } from 'lucide-react'
import { useContext, createContext, useState, useRef, SetStateAction, Dispatch } from 'react'
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

export default function Sidebar({
    expanded,
    setExpanded,
}: {
    expanded: boolean
    setExpanded: Dispatch<SetStateAction<boolean>>
}) {
    return (
        <aside className="h-full flex flex-row bg-midnight border-r">
            <nav className="h-full flex flex-col rounded-sm pt-9 pb-2 max-w-[280px] w-full">
                <SidebarContext.Provider value={{ expanded }}>
                    <ul
                        className={`flex-1 flex flex-col justify-between ${expanded ? 'px-3' : 'px-0 mx-0 w-0 items-center'} pb-2`}
                    >
                        <div>
                            <SidebarHeader expanded={expanded} />
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
        </aside>
    )
}
