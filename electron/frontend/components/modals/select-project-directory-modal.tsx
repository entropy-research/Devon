import FolderPicker from '@/components/ui/folder-picker'
import { useState, lazy, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import useCreateSession from '@/lib/services/sessionService/use-create-session'
import handleNavigate from '@/components/sidebar/handleNavigate'

const Dialog = lazy(() =>
    import('@/components/ui/dialog').then(module => ({
        default: module.Dialog,
    }))
)

const DialogTrigger = lazy(() =>
    import('@/components/ui/dialog').then(module => ({
        default: module.DialogTrigger,
    }))
)

const DialogContent = lazy(() =>
    import('@/components/ui/dialog').then(module => ({
        default: module.DialogContent,
    }))
)

const SelectProjectDirectoryModal = ({
    trigger,
    openProjectModal,
    setOpenProjectModal,
    hideclose,
}: {
    trigger?: JSX.Element
    openProjectModal?: boolean
    setOpenProjectModal?: (open: boolean) => void
    hideclose?: boolean
}) => {
    const [folderPath, setFolderPath] = useState('')
    const [open, setOpen] = useState(false)

    function validate() {
        return folderPath !== ''
    }

    function afterSubmit() {
        setOpen(false)
    }

    function handleOpenChange(open: boolean) {
        setOpen(open)
        if (setOpenProjectModal) setOpenProjectModal(open)
    }

    useEffect(() => {
        if (openProjectModal === undefined) return
        setOpen(openProjectModal)
    }, [openProjectModal])

    return (
        <Dialog open={open} onOpenChange={handleOpenChange}>
            {trigger && <DialogTrigger asChild>{trigger}</DialogTrigger>}
            <DialogContent
                hideclose={hideclose ? true.toString() : false.toString()}
            >
                <div className="mx-8 my-4">
                    <SelectProjectDirectoryComponent
                        folderPath={folderPath}
                        setFolderPath={setFolderPath}
                    />
                    <StartChatButton
                        disabled={!validate()}
                        onClick={afterSubmit}
                        folderPath={folderPath}
                    />
                </div>
            </DialogContent>
        </Dialog>
    )
}

export default SelectProjectDirectoryModal

export const SelectProjectDirectoryComponent = ({
    folderPath,
    setFolderPath,
    disabled = false,
    className,
}: {
    folderPath: string
    setFolderPath: (path: string) => void
    disabled?: boolean
    className?: string
}) => {
    return (
        <div className={`flex flex-col ${className ?? ''}`}>
            <p className="text-xl font-bold mb-4">
                Select your project directory
            </p>
            <FolderPicker
                folderPath={folderPath}
                setFolderPath={setFolderPath}
                disabled={disabled}
            />
        </div>
    )
}

export const StartChatButton = ({ onClick, disabled, folderPath }) => {
    const { createSession, sessionId, loading, error } = useCreateSession()

    function handleStartChat() {
        async function session() {
            try {
                const newSessionId = await createSession(folderPath)
                handleNavigate(newSessionId)
            } catch (error) {
                console.error('Error starting session:', error)
            }
        }
        session()
        onClick()
    }

    return (
        <Button
            disabled={disabled}
            className="bg-primary text-white p-2 rounded-md mt-10 w-full"
            onClick={handleStartChat}
        >
            Start Chat
        </Button>
    )
}
