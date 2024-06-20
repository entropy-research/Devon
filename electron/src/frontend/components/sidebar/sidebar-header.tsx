import { Bot, SquarePen } from 'lucide-react'
import SelectProjectDirectoryModal from '@/components/modals/select-project-directory-modal'

const SidebarHeader = ({ expanded }: { expanded: boolean }) => {
    const handleClick = e => {
        e.preventDefault()
        window.location.href = '/?chat=New' // Change the location
        // window.location.reload() // Force a reload
    }
    return (
        <div
            className={`flex flex-row ${expanded && 'border-b border-outline-day dark:border-outline-night mx-2'} pb-4 items-center justify-between`}
        >
            <>
                <a
                    href="/?chat=New"
                    onClick={handleClick}
                    className="flex mb-6"
                ></a>
                {/* <SelectProjectDirectoryModal
                    trigger={
                        <button className={expanded ? 'visible' : 'hidden'}>
                            <SquarePen size={20} className="text-primary" />
                        </button>
                    }
                /> */}
            </>
        </div>
    )
}

export default SidebarHeader
