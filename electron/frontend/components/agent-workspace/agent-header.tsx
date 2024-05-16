'use client'
import { LayoutGrid } from 'lucide-react'
import { Switch } from '@/components/ui/switch'
import { useState } from 'react'
import { useComingSoonToast } from '@/components/ui/use-toast'

const AgentWorkspaceHeader = ({
    toggleViewMode,
}: {
    toggleViewMode: () => void
}) => {
    const [value, setValue] = useState(false)

    const onChange = () => {
        // if (!value) {
        //     toast()
        // }
        setValue(!value)
        toggleViewMode()
    }
    return (
        <div className="flex flex-row gap-2 items-center absolute z-10 right-10 top-5">
            <p className="text-lg font-semibold">
                {value ? 'Dev Mode' : 'Observe Mode'}
            </p>
            <Switch checked={value} onCheckedChange={onChange} />
        </div>
    )
}

export default AgentWorkspaceHeader
