enum ViewMode {
    Panel,
    Grid,
}

export type File = {
    id: string
    name: string
    path: string
    language: string
    value: any
}

export type Model = {
    id: string
    name: string
    company: string
    comingSoon?: boolean
}


export { ViewMode }
