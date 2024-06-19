export type File = {
    id: string
    name: string
    path: string
    language: string
    value: any
    icon?: string
}

export type Model = {
    id: string
    name: string
    company: string
    comingSoon?: boolean
}

export type Message = {
    text: string
    type: 'user' | 'agent' | 'command' | 'tool' | 'task' | 'thought' | 'error'
}
