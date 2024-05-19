'use client'
import { NotebookPen, GitPullRequest } from 'lucide-react'
import { Switch } from '@/components/ui/switch'
import { useState } from 'react'
import { useComingSoonToast } from '@/components/ui/use-toast'

const AgentWorkspaceHeader = ({
    toggleViewMode,
    visibilityProps: {
        showPlanner,
        setShowPlanner,
        showTimeline,
        setShowTimeline,
    },
}: {
    toggleViewMode: () => void
    visibilityProps: {
        showPlanner: boolean
        setShowPlanner: (show: boolean) => void
        showTimeline: boolean
        setShowTimeline: (show: boolean) => void
    }
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
        <div className="absolute z-10 right-10 top-5 flex gap-5 items-center">
            <div className="flex gap-3">
                <button
                    onClick={() => setShowPlanner(!showPlanner)}
                    className={`w-10 h-10 flex items-center justify-center rounded-md transition duration-200 hover:bg-gray-100 dark:hover:bg-batman ${showPlanner ? 'bg-gray-100 dark:bg-batman' : ''}`}
                >
                    <NotebookPen className="w-5 h-5" />
                </button>
                <button
                    onClick={() => setShowTimeline(!showTimeline)}
                    className={`w-10 h-10 flex items-center justify-center rounded-md transition duration-200 hover:bg-gray-100 dark:hover:bg-batman ${showTimeline ? 'bg-gray-100 dark:bg-batman' : ''}`}
                >
                    <GitPullRequest className="w-5 h-5" />
                </button>
            </div>
            <div className="flex flex-row gap-2 items-center ">
                <p className="text-md font-semibold">
                    {value ? 'Dev Mode' : 'Observe Mode'}
                </p>
                <Switch checked={value} onCheckedChange={onChange} />
            </div>
        </div>
    )
}

export default AgentWorkspaceHeader
