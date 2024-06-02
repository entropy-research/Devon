import { useEffect } from 'react';
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

const FolderPicker = ({ folderPath, setFolderPath, disabled }) => {
    const handleDirectoryPicker = e => {
        window.api.send('get-file-path')
    }

    const handleInputChange = e => {
        setFolderPath(e.target.value)
    }

    useEffect(() => {
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
    }, [])

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
                    disabled={true} // Don't have path validation on input of string yet so disable for now
                />
                <Button className="" onClick={handleDirectoryPicker} disabled={disabled}>
                    Choose...
                </Button>
            </div>
        </div>
    )
}

export default FolderPicker
