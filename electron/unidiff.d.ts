declare module 'unidiff' {
    export interface DiffOptions {
        aname?: string
        bname?: string
        pre_context?: number
        post_context?: number
        context?: number
        format?: 'unified'
    }

    export interface Change {
        count: number
        value: string
        added?: boolean
        removed?: boolean
    }

    export function diffLines(
        oldStr: string | string[],
        newStr: string | string[]
    ): Change[]

    export function formatLines(diff: Change[], options?: DiffOptions): string

    export function diffAsText(
        oldStr: string | string[],
        newStr: string | string[],
        options?: DiffOptions
    ): string
}
