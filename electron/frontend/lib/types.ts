enum ViewMode {
    Panel,
    Grid,
}

enum LocalStorageKey {
    'hasAcceptedCheckbox' = 'hasAcceptedCheckbox',
}

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

export type SessionMachineProps = {
    port: number
    name: string
    path: string
}


export { ViewMode, LocalStorageKey }
