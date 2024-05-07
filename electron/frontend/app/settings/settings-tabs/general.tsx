import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
    CardTitle,
    CardDescription,
    CardHeader,
    CardContent,
    CardFooter,
    Card,
} from '@/components/ui/card'
import { useLocalStorage } from '@/lib/hooks/chat.use-local-storage'
import { LocalStorageKey } from '@/lib/types'
import { useToast } from '@/components/ui/use-toast'
import { useSafeStorage } from '@/lib/services/safeStorageService'

const General = () => {
    const [hasAcceptedCheckbox, setHasAcceptedCheckbox, clearKey] =
        useLocalStorage<boolean>(LocalStorageKey.hasAcceptedCheckbox, false)
    const { toast } = useToast()
    const {
        saveData,
        deleteData,
        checkHasEncryptedData,
    } = useSafeStorage()
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
                    <CardTitle>Anthropic API Key</CardTitle>
                    {!hasEncryptedData && (
                        <CardDescription>Enter your API key.</CardDescription>
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
                                type='password'
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
