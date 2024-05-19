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
    const { toast } = useToast()
    const [hasAcceptedCheckbox, setHasAcceptedCheckbox, clearKey] =
        useLocalStorage<boolean>(LocalStorageKey.hasAcceptedCheckbox, false)

    const handleLocalStorage = () => {
        clearKey()
        toast({ title: 'Local storage cleared!' })
    }

    return (
        <div className="grid gap-6">
            <APIKeyCard name="Anthropic API Key" />
            <APIKeyCard name="OpenAI API Key" comingSoon />
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

const APIKeyCard = ({
    name,
    comingSoon = false,
}: {
    name: string
    comingSoon?: boolean
}) => {
    const { saveData, deleteData, checkHasEncryptedData } = useSafeStorage()
    const [key, setKey] = useState('')
    const [hasEncryptedData, setHasEncryptedData] = useState(false)

    useEffect(() => {
        if (comingSoon) return
        checkHasEncryptedData().then(setHasEncryptedData)
    }, [checkHasEncryptedData])

    return (
        <Card className="bg-midnight">
            <CardHeader>
                <div className="flex items-center">
                    <CardTitle>
                        {name}
                    </CardTitle>
                    <Popover>
                        <PopoverTrigger className="ml-2 mb-2">
                            <CircleHelp size={20} />
                        </PopoverTrigger>
                        <SafeStoragePopoverContent />
                    </Popover>
                    {comingSoon && <p className="text-md px-3 text-neutral-500">(Coming soon!)</p>}
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
                        <Button disabled={comingSoon} onClick={deleteData}>
                            Delete API Key
                        </Button>
                    </div>
                ) : (
                    <div className="flex gap-4 pb-2">
                        <Input
                            disabled={comingSoon}
                            placeholder="API Key"
                            type="password"
                            value={key}
                            onChange={e => setKey(e.target.value)}
                        />
                        {key.length > 0 && (
                            <Button
                                disabled={comingSoon}
                                onClick={() => saveData(key)}
                            >
                                Save
                            </Button>
                        )}
                    </div>
                )}
            </CardContent>
        </Card>
    )
}

export default General
