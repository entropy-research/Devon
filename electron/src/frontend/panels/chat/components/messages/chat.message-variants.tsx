import { Bot, User } from 'lucide-react'
import { cn } from '@/lib/utils'
import { spinner } from '../ui/loading-spinner'
import { Icon } from '@iconify/react'
import { parseDiff } from 'react-diff-view'
import 'react-diff-view/style/index.css'
import './diff-view.css'
import { parseFileDiff } from '../../lib/utils'
import * as unidiff from 'unidiff'
import StyledMessage from './styled-message'
import DiffViewer from '../ui/diff-viewer'

// Different types of message bubbles.

export function UserMessage({ children }: { children: React.ReactNode }) {
    return (
        <div className="group relative flex items-start">
            <div className="flex size-[33px] shrink-0 select-none items-center justify-center rounded-md border bg-background shadow-sm">
                <User />
            </div>
            <div className="ml-4 flex-1 space-y-2 overflow-hidden pl-2">
                {children}
            </div>
        </div>
    )
}

export function BotCard({
    children,
    showAvatar = true,
}: {
    children: React.ReactNode
    showAvatar?: boolean
}) {
    return (
        <div className="group relative flex items-start">
            <div
                className={cn(
                    'flex size-[32px] shrink-0 select-none items-center justify-center rounded-md border bg-primary text-primary-foreground shadow-sm',
                    !showAvatar && 'invisible'
                )}
            >
                <Bot />
            </div>
            <div className="ml-4 flex-1 pl-2">{children}</div>
        </div>
    )
}

export function SystemMessage({ children }: { children: React.ReactNode }) {
    return (
        <div
            className={
                'mt-2 flex items-center justify-center gap-2 text-xs text-gray-500'
            }
        >
            <div className={'max-w-[600px] flex-initial p-2'}>{children}</div>
        </div>
    )
}

export function SpinnerMessage() {
    return (
        <div className="group relative flex items-start">
            <div className="flex size-[32px] shrink-0 select-none items-center justify-center rounded-md border bg-primary text-primary-foreground shadow-sm">
                <Bot />
            </div>
            <div className="ml-4 h-[32px] flex flex-row items-center flex-1 space-y-2 overflow-hidden px-1">
                {spinner}
            </div>
        </div>
    )
}

export const BotMessage = ({
    content,
    className,
}: {
    content: string
    className?: string
}) => {
    const icon = (
        <div className="flex size-[32px] shrink-0 select-none items-center justify-center rounded-md border bg-primary text-primary-foreground shadow-sm">
            <Bot />
        </div>
    )
    return <StyledMessage content={content} className={className} icon={icon} />
}

export const ThoughtMessage = ({
    content,
    className,
}: {
    content: string
    className?: string
}) => {
    const icon = (
        <div className="scale-x-[-1] translate-x-1 flex size-[32px] shrink-0 select-none items-center justify-center rounded-md text-primary-foreground shadow-sm">
            {/* <TfiThought size={28} /> */}
            <Icon
                icon="mdi:thinking"
                className="w-[30px] h-[30px] transform -scale-x-100"
            />
        </div>
    )
    return <StyledMessage content={content} className={className} icon={icon} />
}

export const ToolResponseMessage = ({
    content,
    className,
}: {
    content: string
    className?: string
}) => {
    const icon = <div className="w-[32px]"></div>
    let [command, response] = content.toString().split('|START_RESPONSE|')

    if (command.includes('Running command: edit')) {
        const indexOfFirstNewline = command.indexOf('\n')
        if (indexOfFirstNewline !== -1) {
            command = command.substring(indexOfFirstNewline + 1)
        }
        const { filename, language, searchContent, replaceContent } =
            parseFileDiff(command)

        const resultingDiffLines = unidiff.diffLines(
            searchContent,
            replaceContent
        )
        const unifiedDiff = unidiff.formatLines(resultingDiffLines, {
            aname: 'before',
            bname: 'after',
            context: 3,
        })

        const files = parseDiff(unifiedDiff)

        return (
            <div className="flex ml-[50px]">
                <DiffViewer files={files} />
            </div>
        )
    }
    return <StyledMessage content={command} className={className} icon={icon} />
}
