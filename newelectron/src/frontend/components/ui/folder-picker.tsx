import { useEffect } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

const FolderPicker = ({ folderPath, setFolderPath, disabled = false, showTitle = true, customButton }: {
    folderPath: string
    setFolderPath: (path: string) => void
    disabled?: boolean
    showTitle?: boolean
    customButton?: React.ReactNode
}) => {
    const handleDirectoryPicker = e => {
        //@ts-ignore
        window.api.send('get-file-path')
    }

    const handleInputChange = e => {
        setFolderPath(e.target.value)
    }

    useEffect(() => {
        //@ts-ignore
        window.api.receive('file-path-response', path => {
            if (path === 'cancelled') {
            } else if (path === 'error') {
                console.error(
                    'An error occurred during the directory selection.'
                )
            } else {
                setFolderPath(path)
            }
        })
    }, [])

    return (
        <div className="flex flex-col gap-3">
            {showTitle && <p className="text-md">Local Path</p>}
            <div className="flex justify-between">
                {/* <input>{folderPath}</input> */}
                <Input
                    type="text"
                    className="w-full mr-4 min-w-[300px] disabled:opacity-90" // Remove this after allowing the user to type path
                    value={folderPath}
                    onChange={handleInputChange}
                    disabled={true} // TODO: Don't have path validation on input of string yet so disable for now. See comment above as well
                />
                {customButton ? customButton : <Button
                    className=""
                    onClick={handleDirectoryPicker}
                    disabled={disabled}
                >
                    Choose...
                </Button>}
            </div>
        </div>
    )
}

export default FolderPicker
