'use client'

import { useComingSoonToast } from '@/components/ui/use-toast'
import { Github, Bug, Box, Earth } from 'lucide-react'

const SuggestionContainer = () => {
    return (
        <div className="@container flex flex-col px-6 py-2">
            <p className="text-sm mb-3">Here are some things we can try:</p>
            <div className="flex @xl:flex-row @lg:flex-col flex-col gap-4">
                {suggestions.map(suggestion => (
                    <Suggestion key={suggestion.text} suggestion={suggestion} />
                ))}
            </div>
        </div>
    )
}

const suggestions = [
    {
        text: 'Run my Github repo',
        icon: <Github />,
    },
    {
        text: 'Debug & fix the tests in this codebase',
        icon: <Bug />,
    },
    {
        text: 'Setup an LLM inside a Docker Container',
        icon: <Box />,
    },
    {
        text: 'Create a map of CA wildfires in 2023',
        icon: <Earth />,
    },
]

const Suggestion = ({
    suggestion,
}: {
    suggestion: { text: string; icon: JSX.Element }
}) => {
    const toast = useComingSoonToast()

    return (
        <button
            onClick={toast}
            className="suggestion-item bg-custom-blue text-left transition enabled:hover:cursor-pointer dark:border-transparent md:h-[3.9rem] @xl:w-[16.5rem] @lg:w-full dark:bg-sky/50 flex items-center rounded-xl"
        >
            <div className="px-4">{suggestion.icon}</div>
            <p className="text-xs mr-3 line-clamp-2">{suggestion.text}</p>
        </button>
    )
}

export default SuggestionContainer
