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
    host: string
    name: string
}


export { ViewMode, LocalStorageKey }
