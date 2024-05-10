export default function handleNavigate(sessionId: string) {
    const currentUrl = window.location.href
    const pathname = window.location.pathname
    const search = window.location.search

    // Determine if the current URL is the root or specifically the chat query
    const isRootOrChat =
        pathname === '/' && (!search || search === `?chat=${sessionId}`)

    if (isRootOrChat) {
        // If we're already at the root and the session ID in the query matches or there's no query, just reload
        window.location.reload()
    } else {
        // Otherwise, replace the state to include `?chat={sessionId}` and reload
        window.history.replaceState(
            {},
            '',
            `/${search ? `?chat=${sessionId}` : ''}`
        )
        window.location.reload()
    }
}
