// Source: https://github.com/OpenDevin/OpenDevin/blob/main/frontend/src/components/Browser.tsx
export default function BrowserPanel(): JSX.Element {
    const url = ''
    const screenshotSrc = ''

    const imgSrc =
        screenshotSrc &&
        (screenshotSrc as string).startsWith('data:image/png;base64,')
            ? screenshotSrc
            : `data:image/png;base64,${screenshotSrc || ''}`

    return (
        <div className="h-full m-2 w-full flex items-start flex-col">
            <div className="p-2 flex items-center pb-2 w-full">
                <div className="flex space-x-2 ml-2 mr-4">
                    <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                    <div className="w-3 h-3 bg-yellow-400 rounded-full"></div>
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                </div>
                <input
                    type="text"
                    className="flex-grow rounded-full px-5 py-2 overflow-x-auto text-gray-700 mr-2"
                    placeholder="https://"
                    value={url}
                    readOnly
                />
            </div>
            {screenshotSrc ? (
                <img
                    src={imgSrc}
                    alt="Browser Screenshot"
                    style={{ maxWidth: '100%', height: 'auto' }}
                />
            ) : (
                <p className="text-lg flex justify-center items-center h-full w-full">
                    Coming soon!
                </p>
            )}
        </div>
    )
}
