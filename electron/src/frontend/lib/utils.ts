import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}

// Path utils
function addTrailingSlash(str: string) {
    if (!str.endsWith('/')) {
        return str + '/'
    }
    return str
}

function removeTrailingSlash(str: string) {
    if (str.endsWith('/')) {
        return str.slice(0, -1)
    }
    return str
}

export function getRelativePath(fullPath: string, projectPath: string) {
    return fullPath.replace(addTrailingSlash(projectPath), '')
}

export function getFileName(path: string) {
    return removeTrailingSlash(path).split('/').pop() || ''
}


export const parseCommand = (content: string) => {
    const regex = /Running command: (\S+)\s*([\s\S]*)/
    const match = content.match(regex)

    if (match) {
        const [, command, remainingText] = match

        return {
            command: command.trim(),
            remainingText: remainingText.trim(),
        }
    }

    return null // Return null if no command is found
}