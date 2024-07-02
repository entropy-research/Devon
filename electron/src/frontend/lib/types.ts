export type File<T = any> = {
    id: string
    name: string
    path: string
    language: string
    value: T
    icon?: string
    agentHasOpen?: boolean
}

export type Model = {
    id: string
    name: string
    company: string
    comingSoon?: boolean
    apiKeyUrl?: string
}

export type Message = {
    text: string
    type:
        | 'user'
        | 'agent'
        | 'command'
        | 'tool'
        | 'task'
        | 'thought'
        | 'error'
        | 'shellCommand'
        | 'shellResponse'
        | 'rateLimit'
}
