import { useState, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
    CardTitle,
    CardDescription,
    CardHeader,
    CardContent,
    Card,
} from '@/components/ui/card'
import { useLocalStorage } from '@/lib/hooks/chat.use-local-storage'
import { LocalStorageKey } from '@/lib/types'
import { useToast } from '@/components/ui/use-toast'
import { useSafeStorage } from '@/lib/services/safeStorageService'
import { Popover, PopoverTrigger } from '@/components/ui/popover'
import { CircleHelp } from 'lucide-react'
import SafeStoragePopoverContent from '@/components/safe-storage-popover-content'
import { Skeleton } from '@/components/ui/skeleton'
import { Model } from '@/lib/types'
import { models } from '@/lib/config'

const General = () => {
    const { toast } = useToast()
    const [hasAcceptedCheckbox, setHasAcceptedCheckbox, clearKey] =
        useLocalStorage<boolean>(LocalStorageKey.hasAcceptedCheckbox, false)

    const handleLocalStorage = () => {
        clearKey()
        toast({ title: 'Local storage cleared!' })
    }

    return (
        <div className="grid gap-6 pt-20 pb-20 max-w-2xl mx-auto">
            <Card className="bg-midnight">
                <CardHeader>
                    <div className="flex items-center -mb-2">
                        <CardTitle>API Keys</CardTitle>
                        <Popover>
                            <PopoverTrigger className="ml-2 mb-2">
                                <CircleHelp size={20} />
                            </PopoverTrigger>
                            <SafeStoragePopoverContent />
                        </Popover>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="grid gap-6">
                        {models.map((model: Model) => (
                            <APIKeyComponent key={model.id} model={model} />
                        ))}
                    </div>
                </CardContent>
            </Card>
            <Card className="bg-midnight">
                <CardHeader>
                    <CardTitle>Miscellaneous</CardTitle>
                </CardHeader>
                <CardContent>
                    <Button className="w-fit" onClick={handleLocalStorage}>
                        Clear Local Storage
                    </Button>
                </CardContent>
            </Card>
        </div>
    )
}

const APIKeyComponent = ({ model }: { model: Model }) => {
    const { addApiKey, getApiKey, removeApiKey } = useSafeStorage()
    const [key, setKey] = useState('')
    const [isKeyStored, setIsKeyStored] = useState(false)
    const [isLoading, setIsLoading] = useState(true)
    const [isSaving, setIsSaving] = useState(false)

    const fetchApiKey = useCallback(async () => {
        if (model.comingSoon) {
            setIsLoading(false)
            return
        }
        setIsLoading(true)
        const res = await getApiKey(model.id)
        if (res) {
            setKey(res)
            setIsKeyStored(true)
        }
        setIsLoading(false)
    }, [model.id])

    useEffect(() => {
        fetchApiKey()
    }, [])

    const handleSave = async () => {
        setIsSaving(true)
        await addApiKey(model.id, key)
        setIsKeyStored(true)
        setIsSaving(false)
    }

    const handleDelete = async () => {
        setIsSaving(true)
        await removeApiKey(model.id)
        setIsKeyStored(false)
        setKey('')
        setIsSaving(false)
    }

    return (
        <div>
            <div className="flex items-center mb-2">
                <p className="text-lg">{model.name}</p>
                {model.comingSoon && (
                    <p className="text-md px-2 text-neutral-500">
                        (Coming soon!)
                    </p>
                )}
            </div>
            {isLoading ? (
                <Skeleton className="h-10 w-full" />
            ) : isKeyStored ? (
                <div className="flex gap-4">
                    <Input
                        type="password"
                        value="**********************"
                        disabled
                    />
                    <Button
                        disabled={model.comingSoon || isSaving}
                        onClick={handleDelete}
                    >
                        {isSaving ? 'Deleting...' : 'Delete API Key'}
                    </Button>
                </div>
            ) : (
                <div className="flex gap-4">
                    <Input
                        id={model.id}
                        disabled={model.comingSoon || isSaving}
                        placeholder={`${model.company} API Key`}
                        type="password"
                        value={key}
                        onChange={e => setKey(e.target.value)}
                    />
                    {key.length > 0 && (
                        <Button
                            disabled={model.comingSoon || isSaving}
                            onClick={handleSave}
                        >
                            {isSaving ? 'Saving...' : 'Save'}
                        </Button>
                    )}
                </div>
            )}
        </div>
    )
}

export default General
