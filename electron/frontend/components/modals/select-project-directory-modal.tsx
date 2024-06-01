import FolderPicker from '@/components/ui/folder-picker'
import { useState, lazy, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import handleNavigate from '@/components/sidebar/handleNavigate'
import { nanoid } from '@/lib/chat.utils'
import { ArrowLeft } from 'lucide-react'
import {
    useReadSessions,
    useDeleteSession,
} from '@/lib/services/sessionService/sessionHooks'
import { useSearchParams } from 'next/navigation'

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
    header,
}: {
    trigger?: JSX.Element
    openProjectModal?: boolean
    setOpenProjectModal?: (open: boolean) => void
    hideclose?: boolean
    header?: JSX.Element
}) => {
    const [folderPath, setFolderPath] = useState('')
    const [open, setOpen] = useState(false)
    const [page, setPage] = useState(1)
    const { sessions, loading, error, refreshSessions } = useReadSessions()

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
                    {sessions?.length > 0 && page === 1 ? (
                        <ExistingSessionFound
                            sessions={sessions}
                            setPage={setPage}
                            onClick={afterSubmit}
                        />
                    ) : sessions?.length === 0 || page === 2 ? (
                        <>
                            {page !== 1 && (
                                <button
                                    className="top-3 left-3 absolute text-primary mb-2 flex items-center p-1"
                                    onClick={() => setPage(1)}
                                >
                                    <ArrowLeft size={18} className="mr-1" />
                                    {/* {'Back'} */}
                                </button>
                            )}
                            {/* {header} */}
                            <SelectProjectDirectoryComponent
                                folderPath={folderPath}
                                setFolderPath={setFolderPath}
                            />
                            <StartChatButton
                                disabled={!validate()}
                                onClick={afterSubmit}
                                folderPath={folderPath}
                            />
                        </>
                    ) : (
                        <></>
                    )}
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
            <p className="text-lg font-bold mb-4">
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
    function handleStartChat() {
        async function session() {
            try {
                // const newSessionId = nanoid()
                // Using a set session id for now: for single sessions
                const newSessionId = 'New chat'
                handleNavigate(newSessionId, folderPath)
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

const ExistingSessionFound = ({ sessions, setPage, onClick }) => {
    const searchParams = useSearchParams()
    function handleContinueChat() {
        async function session() {
            try {
                // Don't need to navigate if already on chat
                if (searchParams.get('chat') === 'New chat') {
                    return
                }
                // const newSessionId = nanoid()
                // Using a set session id for now: for single sessions
                const newSessionId = 'New chat'
                handleNavigate(newSessionId)
            } catch (error) {
                console.error('Error starting session:', error)
            }
        }
        session()
        onClick()
    }
    return (
        <div>
            {sessions?.length > 0 && sessions[0] === 'New chat' ? (
                <div>
                    <p className="text-2xl font-bold">
                        Continue previous chat?
                    </p>
                    <p className="text-md mt-2 text-neutral-400">
                        {`Previous task: "`}
                        <span className="italic">Create a snake game</span>
                        {`"`}
                    </p>
                    <div className="flex flex-col items-center">
                        <Button
                            type="submit"
                            className="bg-primary text-white p-2 rounded-md w-full mt-7"
                            onClick={handleContinueChat}
                        >
                            Continue
                        </Button>
                        <div className="bg-neutral-600 h-[1px] w-full mt-8 mb-1"></div>
                        <p className="text-md m-4 mb-5">Or start a new chat</p>
                        <Button
                            variant="outline"
                            className="text-[#977df5] p-2 rounded-md mt-0 w-full font-bold"
                            onClick={() => setPage(2)}
                        >
                            New Chat
                        </Button>
                    </div>
                </div>
            ) : (
                <></>
            )}
        </div>
    )
}
