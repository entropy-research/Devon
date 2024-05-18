'use client'
import { List, PanelsTopLeft, PanelLeft } from 'lucide-react'
import { useState } from 'react'
import Sidebar from '@/components/sidebar/sidebar'

const HeaderSidebar = () => {
    const [expanded, setExpanded] = useState(false)

    return (
        <>
            <div className="bg-night flex w-full absolute top-0 p-4">
                <button onClick={() => setExpanded(!expanded)} className="p-2">
                    <PanelsTopLeft />
                </button>
            </div>
            <Sidebar expanded={expanded} setExpanded={setExpanded} />
        </>
    )
}

export default HeaderSidebar
