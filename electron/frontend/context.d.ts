/* ********************************************************************
 *   Declaration file for the API exposed over the context bridge
 *********************************************************************/

// export interface IBloopAPI {
//     foo: string
//     ping: () => Promise<string>
// }

declare global {
    interface Window {
        // BloopAPI: IBloopAPI,
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
        }
    }
}
