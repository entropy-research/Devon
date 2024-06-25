import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { CardContent, Card } from '@/components/ui/card'
import { Dialog, DialogTrigger, DialogContent } from '@/components/ui/dialog'
import FolderPicker from '@/components/ui/folder-picker'
import axios from 'axios'
import { SessionMachineContext } from '@/contexts/session-machine-context'
import { Check } from 'lucide-react'
import CircleSpinner from '@/components/ui/circle-spinner/circle-spinner'
import { Skeleton } from '@/components/ui/skeleton'

type IndexStatus = 'running' | 'done' | 'error'

interface IndexItem {
    path: string
    status: IndexStatus
}

const IndexesModal = ({ trigger }: { trigger: JSX.Element }) => {
    const [open, setOpen] = useState(false)
    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>{trigger}</DialogTrigger>
            <DialogContent className="w-full max-w-[650px]">
                <IndexList setOpen={setOpen} />
            </DialogContent>
        </Dialog>
    )
}

const IndexList = ({ setOpen }: { setOpen: (val: boolean) => void }) => {
    const host = SessionMachineContext.useSelector(state => state.context.host)
    const sessionActorref = SessionMachineContext.useActorRef()
    const [indexes, setIndexes] = useState<IndexItem[]>([])
    const [newIndexPath, setNewIndexPath] = useState('')
    const [error, setError] = useState<string | null>(null)
    const [selectedIndex, setSelectedIndex] = useState<string | null>(null)

    useEffect(() => {
        fetchIndexes()
    }, [])

    useEffect(() => {
        const interval = setInterval(() => {
            indexes.forEach(index => {
                if (index.status !== 'done') {
                    checkIndexStatus(index.path)
                }
            })
        }, 3000)
        return () => clearInterval(interval)
    }, [indexes])

    const fetchIndexes = async () => {
        try {
            const response = await axios.get(`${host}/indexes`)
            setIndexes(response.data)
        } catch (error) {
            console.error('Failed to fetch indexes:', error)
            setError('Failed to fetch indexes. Please try again.')
        }
    }

    const handleRemoveIndex = async (path: string) => {
        try {
            const encodedPath = encodeURIComponent(path.replace(/\//g, '%2F'))
            await axios.delete(`${host}/indexes/${encodedPath}`)
            setIndexes(indexes.filter(index => index.path !== path))
        } catch (error) {
            console.error('Failed to remove index:', error)
            setError('Failed to remove index. Please try again.')
        }
    }

    const handleAddIndex = async () => {
        if (newIndexPath) {
            try {
                setError(null)
                const encodedPath = encodeURIComponent(
                    newIndexPath.replace(/\//g, '%2F')
                )
                await axios.delete(`${host}/indexes/${encodedPath}`)
                await axios.post(`${host}/indexes/${encodedPath}`)

                setIndexes([
                    ...indexes,
                    { path: newIndexPath, status: 'running' },
                ])
                setNewIndexPath('')
                checkIndexStatus(newIndexPath)
            } catch (error) {
                console.error('Failed to add index:', error)
                setError('Failed to add index. Please try again.')
            }
        }
    }

    const checkIndexStatus = async (path: string) => {
        const encodedPath = encodeURIComponent(path.replace(/\//g, '%2F'))
        try {
            const response = await axios.get(
                `${host}/indexes/${encodedPath}/status`
            )
            const status = response.data
            setIndexes(prevIndexes =>
                prevIndexes.map(index =>
                    index.path === path ? { ...index, status } : index
                )
            )
        } catch (error) {
            console.error('Failed to get index status:', error)
            setIndexes(prevIndexes =>
                prevIndexes.map(index =>
                    index.path === path ? { ...index, status: 'error' } : index
                )
            )
        }
    }

    const handleIndexSelection = (path: string) => {
        setSelectedIndex(prevIndex => (prevIndex === path ? null : path))
    }

    const handleStartChat = () => {
        if (selectedIndex) {
            sessionActorref.send({
                type: 'session.delete',
            })
            const searchParams = new URLSearchParams(window.location.search)
            searchParams.set('path', encodeURIComponent(selectedIndex))
            setOpen(false)
        }
    }

    return (
        <div className="pt-4 pb-2 px-2 flex flex-col gap-5">
            <Card className="bg-midnight">
                <CardContent className="mt-5 w-full">
                    <h2 className="text-lg font-semibold mb-4">
                        Directory indexes
                    </h2>
                    <div className="flex items-center mb-2 gap-4">
                        <FolderPicker
                            folderPath={newIndexPath}
                            setFolderPath={setNewIndexPath}
                            showTitle={false}
                            buttonClassName="px-5"
                        />
                        {newIndexPath && (
                            <Button onClick={handleAddIndex}>
                                Create an Index
                            </Button>
                        )}
                    </div>
                    {error && (
                        <div className="text-red-500 mb-2 mt-6">{error}</div>
                    )}
                    {indexes.length > 0 && (
                        <div className={'mt-6'}>
                            {indexes.map(index => (
                                <IndexItemComponent
                                    key={index.path}
                                    index={index}
                                    onRemove={handleRemoveIndex}
                                    isSelected={selectedIndex === index.path}
                                    onSelect={handleIndexSelection}
                                />
                            ))}
                            {selectedIndex && (
                                <div className="w-full flex flex-col items-center mt-4">
                                    <p className="text-md mb-4 font-semibold">
                                        Start a new chat with this index?
                                    </p>
                                    <Button
                                        onClick={handleStartChat}
                                        className="px-5"
                                    >
                                        New Chat
                                    </Button>
                                </div>
                            )}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}

const IndexItemComponent = ({
    index,
    onRemove,
    onSelect,
    isSelected,
}: {
    index: IndexItem
    onRemove: (path: string) => void
    onSelect: (path: string) => void
    isSelected: boolean
}) => {
    return (
        <div className="py-2 w-full flex flex-col items-center">
            <div className="flex items-center justify-between gap-2 w-full">
                <div
                    className={`flex items-center flex-grow mr-2 relative ${
                        index.status === 'done'
                            ? 'cursor-pointer'
                            : 'cursor-not-allowed'
                    }`}
                    onClick={() => {
                        if (index.status === 'done') {
                            onSelect(index.path)
                        }
                    }}
                >
                    {index.status === 'done' ? (
                        <div
                            className={`w-4 h-4 rounded-full border-[1.5px] mr-2 flex items-center justify-center ${
                                isSelected
                                    ? 'border-primary border'
                                    : 'border-input'
                            }`}
                        >
                            {isSelected && (
                                <div className="w-[7px] h-[7px] rounded-full bg-primary absolute" />
                            )}
                        </div>
                    ) : (
                        <Skeleton className="w-4 h-4 rounded-full mr-2"></Skeleton>
                    )}
                    <Input
                        value={index.path}
                        readOnly
                        className={`flex-1 bg-night border-none pr-8 text-ellipsis ${
                            index.status !== 'done'
                                ? 'cursor-not-allowed text-neutral-500'
                                : 'cursor-pointer text-white'
                        }`}
                    />
                    {index.status === 'done' ? (
                        <Check
                            className="text-green-500 absolute right-2"
                            size={14}
                        />
                    ) : index.status === 'running' ? (
                        <CircleSpinner
                            className="absolute right-2"
                            color="#636363"
                        />
                    ) : (
                        <p>{index.status}</p>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    {index.status === 'error' && (
                        <span className="text-red-500">Error</span>
                    )}
                    <Button
                        onClick={() => onRemove(index.path)}
                        variant="outline-thin"
                        disabled={index.status !== 'done'}
                        className="w-[88px]"
                    >
                        {index.status === 'running' ? 'Indexing...' : `Remove`}
                    </Button>
                </div>
            </div>
            {index.status === 'running' && (
                <span className="text-sm mt-2 text-neutral-500">
                    This directory is being indexed... feel free to close the
                    tab and check back later!
                </span>
            )}
        </div>
    )
}

export default IndexesModal
