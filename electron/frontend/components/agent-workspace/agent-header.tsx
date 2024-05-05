'use client'
import { LayoutGrid } from 'lucide-react'
import { Switch } from '@/components/ui/switch'
import { useState } from 'react'

const AgentWorkspaceHeader = ({
    toggleViewMode,
}: {
    toggleViewMode: () => void
}) => {
    const [value, setValue] = useState(true)

    const onChange = () => {
        setValue(!value)
    }
    return (
        <div className="flex flex-row justify-between items-start">
            <h1 className="font-bold text-lg mb-5">{`Devon's Workspace`}</h1>

            <div className="flex flex-row gap-4 items-center">
                <button onClick={toggleViewMode}>
                    <LayoutGrid className="w-5 h-5 text-primary" />
                </button>
                <div className="flex flex-row gap-2 items-center">
                    <Switch checked={value} onCheckedChange={onChange} />
                    <p className="text-sm font-semibold">
                        {value ? 'Following' : 'Follow'}
                    </p>
                </div>
            </div>
        </div>
    )
}

export default AgentWorkspaceHeader
