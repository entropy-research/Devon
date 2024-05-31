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
}

export { ViewMode, LocalStorageKey }
