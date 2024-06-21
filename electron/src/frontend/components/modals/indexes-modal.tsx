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

type IndexStatus = 'pending' | 'done' | 'error'

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
    const [indexes, setIndexes] = useState<string[]>([])
    const [indexStatuses, setIndexStatuses] = useState<
        Record<string, IndexStatus>
    >({})
    const [newIndexPath, setNewIndexPath] = useState('')
    const [error, setError] = useState<string | null>(null)
    const [selectedIndex, setSelectedIndex] = useState<string | null>(null)

    useEffect(() => {
        fetchIndexes()
    }, [])

    useEffect(() => {
        const interval = setInterval(() => {
            indexes.forEach(index => {
                if (indexStatuses[index] !== 'done') {
                    checkIndexStatus(index)
                }
            })
        }, 5000)
        return () => clearInterval(interval)
    }, [indexes, indexStatuses])

    const fetchIndexes = async () => {
        try {
            const response = await axios.get(`${host}/indexes`)
            setIndexes(response.data)
            const statuses: Record<string, IndexStatus> = {}
            response.data.forEach((index: string) => {
                statuses[index] = 'done'
            })
            setIndexStatuses(statuses)
        } catch (error) {
            console.error('Failed to fetch indexes:', error)
            setError('Failed to fetch indexes. Please try again.')
        }
    }

    const handleRemoveIndex = async (path: string) => {
        try {
            const encodedPath = encodeURIComponent(path.replace(/\//g, '%2F'))
            await axios.delete(`${host}/indexes/${encodedPath}`)
            setIndexes(indexes.filter(index => index !== path))
            setIndexStatuses(prev => {
                const newStatuses = { ...prev }
                delete newStatuses[path]
                return newStatuses
            })
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

                setIndexes([...indexes, newIndexPath])
                setIndexStatuses(prev => ({
                    ...prev,
                    [newIndexPath]: 'pending',
                }))
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
            setIndexStatuses(prev => ({ ...prev, [path]: status }))
        } catch (error) {
            console.error('Failed to get index status:', error)
            setIndexStatuses(prev => ({ ...prev, [path]: 'error' }))
        }
    }

    const handleIndexSelection = (index: string) => {
        setSelectedIndex(prevIndex => (prevIndex === index ? null : index))
    }

    const handleStartChat = () => {
        if (selectedIndex) {
            // Implement the logic to start a chat with the selected index
            console.log(`Starting chat with index: ${selectedIndex}`)
            // You might want to close the modal or navigate to a chat interface here
            setOpen(false)
        }
    }

    return (
        <div className="pt-4 pb-2 px-2 flex flex-col gap-5">
            <Card className="bg-midnight">
                <CardContent className="mt-5 w-full">
                    <h2 className="text-lg font-semibold mb-4">
                        Directory Indexes
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
                    {indexes && indexes.length > 0 && (
                        <div className={'mt-6'}>
                            {indexes.map(index => (
                                <IndexItem
                                    key={index}
                                    index={index}
                                    status={indexStatuses[index]}
                                    onRemove={handleRemoveIndex}
                                    deselect={() =>
                                        selectedIndex === index &&
                                        setSelectedIndex(undefined)
                                    }
                                    isSelected={selectedIndex === index}
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
                                        // className="w-2/3"
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

const IndexItem = ({
    index,
    status,
    onRemove,
    onSelect,
    isSelected,
}: {
    index: string
    status: IndexStatus
    onRemove: (path: string) => void
    onSelect: (index: string) => void
    isSelected: boolean
}) => {
    return (
        <div className="flex items-center justify-between py-2">
            <div
                className={`flex items-center flex-grow mr-4 relative ${
                    status === 'done' ? 'cursor-pointer' : 'cursor-not-allowed'
                }`}
                onClick={() => {
                    if (status === 'done') {
                        onSelect(index)
                    }
                }}
            >
                {status === 'done' ? (
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
                    value={index}
                    readOnly
                    className="bg-night border-none text-white pr-8 text-ellipsis"
                />
                {status === 'done' ? (
                    <Check
                        className="text-green-500 absolute right-2"
                        size={14}
                    />
                ) : (
                    <CircleSpinner className="text-green-500 absolute right-2" />
                )}
            </div>
            <div className="flex items-center gap-2">
                {status === 'error' && (
                    <span className="text-red-500">Error</span>
                )}
                <Button
                    onClick={() => onRemove(index)}
                    variant="outline-thin"
                    disabled={status !== 'done'}
                    className="w-[88px]"
                >
                    {status !== 'done' ? 'Indexing...' : `Remove`}
                </Button>
            </div>
        </div>
    )
}

export default IndexesModal
