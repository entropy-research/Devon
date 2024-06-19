export function getPlatform() {
    const arch = process.arch === 'x64' ? 'x86_64' : process.arch
    return {
        platform: process.platform,
        arch: arch,
    }
}
