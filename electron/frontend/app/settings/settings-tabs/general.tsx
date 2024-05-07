import { useState, useEffect } from 'react'
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
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from '@/components/ui/popover'
import { CircleHelp } from 'lucide-react'
import SafeStoragePopoverContent from '@/components/safe-storage-popover-content'

const General = () => {
    const [hasAcceptedCheckbox, setHasAcceptedCheckbox, clearKey] =
        useLocalStorage<boolean>(LocalStorageKey.hasAcceptedCheckbox, false)
    const { toast } = useToast()
    const { saveData, deleteData, checkHasEncryptedData } = useSafeStorage()
    const [key, setKey] = useState('')
    const [hasEncryptedData, setHasEncryptedData] = useState(false)

    useEffect(() => {
        checkHasEncryptedData().then(setHasEncryptedData)
    }, [checkHasEncryptedData])

    const handleLocalStorage = () => {
        clearKey()
        toast({ title: 'Local storage cleared!' })
    }

    return (
        <div className="grid gap-6">
            <Card>
                <CardHeader>
                    <div className="flex items-center">
                        <CardTitle>Anthropic API Key</CardTitle>
                        <Popover >
                            <PopoverTrigger className="ml-2 mb-2">
                                <CircleHelp size={20} />
                            </PopoverTrigger>
                            {hasEncryptedData ? (
                                <PopoverContent
                                    side="top"
                                    className="bg-night w-fit p-2"
                                >
                                    To edit, go to settings
                                </PopoverContent>
                            ) : (
                                <SafeStoragePopoverContent />
                            )}
                        </Popover>
                    </div>
                    {!hasEncryptedData && (
                        <CardDescription>Enter your API key</CardDescription>
                    )}
                </CardHeader>
                <CardContent>
                    {hasEncryptedData ? (
                        <div className="flex gap-4">
                            <Input
                                type="password"
                                value="**********************"
                                disabled
                            />
                            <Button onClick={deleteData}>Delete API Key</Button>
                        </div>
                    ) : (
                        <div className="flex gap-4 pb-2">
                            <Input
                                placeholder="API Key"
                                type="password"
                                value={key}
                                onChange={e => setKey(e.target.value)}
                            />
                            {key.length > 0 && (
                                <Button onClick={() => saveData(key)}>
                                    Save
                                </Button>
                            )}
                        </div>
                    )}
                </CardContent>
            </Card>
            <Card>
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

export default General
