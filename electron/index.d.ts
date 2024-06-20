/* ********************************************************************
 *   Declaration file for the API exposed over the context bridge
 *********************************************************************/
export {}

declare global {
    interface Window {
        api: {
            invoke: (channel: string, ...args: any[]) => Promise<any>
            receive: (
                channel: string,
                listener: (...args: any[]) => void
            ) => void
            remove: (
                channel: string,
                listener: (...args: any[]) => void
            ) => void
            send: (channel: string, ...args: any[]) => void
            removeAllListeners: (channel: string) => void
        }
    }
}
