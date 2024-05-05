import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

const FolderPicker = ({ folderPath, setFolderPath }) => {
    const handleDirectoryPicker = e => {
        window.api.send('get-file-path')
    }

    const handleInputChange = e => {
        setFolderPath(e.target.value)
    }

    window.api.receive('file-path-response', path => {
        if (path === 'cancelled') {
            console.log('Directory selection was cancelled.')
        } else if (path === 'error') {
            console.error('An error occurred during the directory selection.')
        } else {
            console.log('Selected directory:', path)
            setFolderPath(path)
        }
    })

    return (
        <div className="flex flex-col gap-3">
            <p className="text-md">Local Path</p>
            <div className="flex gap-4">
                {/* <input>{folderPath}</input> */}
                <Input
                    type="text"
                    className="w-[300px]"
                    value={folderPath}
                    onChange={handleInputChange}
                />
                <Button className="" onClick={handleDirectoryPicker}>
                    Choose...
                </Button>
            </div>
        </div>
    )
}

export default FolderPicker
