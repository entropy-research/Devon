export default function handleNavigate(sessionId: string, path?: string) {
    const currentUrl = window.location.href
    const pathname = window.location.pathname
    const searchParams = new URLSearchParams(window.location.search)

    // Encode the path

    // Set the search parameters
    searchParams.set('chat', sessionId)
    if (path) {
        searchParams.set('path', encodeURIComponent(path))
    }

    // Construct the new search string
    const newSearch = searchParams.toString()

    // Determine if the current URL is the root or specifically the chat query
    const isRootOrChat =
        pathname === '/' &&
        (!window.location.search ||
            window.location.search === `?chat=${sessionId}`)

    if (isRootOrChat) {
        // If we're already at the root and the session ID in the query matches or there's no query, just reload
        // window.location.reload()
    } else {
        // Otherwise, replace the state to include `?chat={sessionId}&path={encodedPath}` and reload
        window.history.replaceState({}, '', `/?${newSearch}`)
        // window.location.reload()
    }
}
