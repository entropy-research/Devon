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
                        />
                        {newIndexPath && (
                            <Button onClick={handleAddIndex}>Add Index</Button>
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
                                />
                            ))}
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
}: {
    index: string
    status: IndexStatus
    onRemove: (path: string) => void
}) => {
    return (
        <div className="flex items-center justify-between py-2">
            <div className="flex items-center flex-grow mr-4 relative">
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
                {/* {status === 'pending' && (
                    <span className="text-yellow-500">Indexing...</span>
                )} */}
                {/* {status !== 'done' && (
                    <span className="text-yellow-500">Indexing...</span>
                )} */}
                {status === 'error' && (
                    <span className="text-red-500">Error</span>
                )}
                <Button
                    onClick={() => onRemove(index)}
                    variant="outline-thin"
                    // disabled={status === 'pending'}
                    disabled={status !== 'done'}
                    className="min-w-[82px]"
                >
                    {status !== 'done' ? 'Indexing...' : `Remove`}
                </Button>
            </div>
        </div>
    )
}

export default IndexesModal
