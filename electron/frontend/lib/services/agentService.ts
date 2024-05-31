export async function spawnDevonAgent() {
    const res: {
        success: boolean
        message?: string
    } = await window.api.invoke('spawn-devon-agent')
    return res
}
