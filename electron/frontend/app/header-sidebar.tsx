'use client'
import { List, PanelsTopLeft, PanelLeft, SquarePen } from 'lucide-react'
import { useState } from 'react'
import Sidebar from '@/components/sidebar/sidebar'
import SelectProjectDirectoryModal from '@/components/modals/select-project-directory-modal'

const HeaderSidebar = () => {
    const [expanded, setExpanded] = useState(false)

    return (
        <>
            <div className="flex w-full absolute top-0 px-4 pt-3 items-center gap-2 pb-1">
                <button onClick={() => setExpanded(!expanded)} className="p-2">
                    <PanelsTopLeft size="1.4rem"/>
                </button>
                <a href="/" className="text-white text-xl font-semibold">
                    Devon
                </a>
                <SelectProjectDirectoryModal
                    trigger={
                        <button
                            className={`ml-[96px] p-2 ${expanded ? 'visible' : 'hidden'}`}
                        >
                            <SquarePen size="1.3rem" className="text-primary" />
                        </button>
                    }
                    header={<h1 className="text-2xl font-bold mb-5">Create new chat</h1>}
                />
            </div>
            <Sidebar expanded={expanded} setExpanded={setExpanded} />
        </>
    )
}

export default HeaderSidebar
