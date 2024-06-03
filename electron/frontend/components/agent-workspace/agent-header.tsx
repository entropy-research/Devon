'use client'
import { useState, useEffect } from 'react'
import {
    NotebookPen,
    GitPullRequest,
    LayoutPanelLeft,
    Columns2,
} from 'lucide-react'
import { Switch } from '@/components/ui/switch'
import { useComingSoonToast } from '@/components/ui/use-toast'
import { ViewMode } from '@/lib/types'

const AgentWorkspaceHeader = ({
    viewMode,
    toggleViewMode,
    visibilityProps: {
        showPlanner,
        setShowPlanner,
        showTimeline,
        setShowTimeline,
    },
}: {
    viewMode: ViewMode
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
    useEffect(() => {}, [value])

    return (
        <div className="absolute z-10 right-10 top-2 flex gap-2 items-center h-10">
            {showTimeline && (
                <div className="flex gap-3">
                    {/* <button
                    onClick={() => setShowPlanner(!showPlanner)}
                    className={`w-10 h-10 flex items-center justify-center rounded-md transition duration-200 hover:bg-gray-100 dark:hover:bg-batman ${showPlanner ? 'bg-gray-100 dark:bg-batman' : ''}`}
                >
                    <NotebookPen className="w-5 h-5" />
                </button> */}
                    <button
                        onClick={toggleViewMode}
                        // className={`flex p-2 items-center justify-center rounded-md transition duration-200 hover:bg-gray-100 dark:hover:bg-batman ${viewMode === ViewMode.Panel ? 'bg-gray-100 dark:bg-batman' : ''}`}
                        className={`flex p-2 items-center justify-center rounded-md transition duration-200 hover:bg-gray-100 dark:hover:bg-batman`}
                    >
                        {viewMode === ViewMode.Panel ? (
                            <Columns2 size="1.4rem" />
                        ) : (
                            <LayoutPanelLeft size="1.3rem" />
                        )}
                    </button>
                </div>
            )}
            <div className="flex flex-row gap-2 items-center ">
                <p className="text-md font-semibold">Show Timeline</p>
                <Switch
                    checked={showTimeline}
                    onCheckedChange={() => setShowTimeline(!showTimeline)}
                />
            </div>
        </div>
    )
}

export default AgentWorkspaceHeader

export const ToggleTimelineHeader = ({
    showTimeline,
    setShowTimeline,
}: {
    showTimeline: boolean
    setShowTimeline: (show: boolean) => void
}) => {
    return (
        <div className="flex flex-row gap-2 items-center mr-5 absolute right-0">
            <button
                className={`border border-neutral-500 rounded-md pl-4 pr-3 flex p-2 items-center justify-center rounded-md transition duration-200 hover:bg-gray-100 dark:hover:bg-batman ${showTimeline ? 'bg-gray-100 dark:bg-batman' : ''}`}
                onClick={() => setShowTimeline(!showTimeline)}
            >
                <p className="mr-2 font-bold">Timeline</p>
                <GitPullRequest size="1.3rem" />
            </button>
        </div>
    )
}
