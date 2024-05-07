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

const General = () => {
    const [_, setHasAcceptedCheckbox, clearKey] = useLocalStorage<boolean>(
        LocalStorageKey.hasAcceptedCheckbox,
        false
    )
    const { toast } = useToast()

    function handleLocalStorage() {
        clearKey()
        toast({
            title: 'Cleared!',
        })
    }

    return (
        <div className="grid gap-6">
            <Card>
                <CardHeader>
                    <CardTitle>API Key</CardTitle>
                    <CardDescription>Enter your API key.</CardDescription>
                </CardHeader>
                <CardContent>
                    <form className="flex flex-col gap-4">
                        <Input placeholder="API Key" type="password" />
                    </form>
                </CardContent>
                <CardFooter className="border-t px-6 py-4">
                    <Button>Save</Button>
                </CardFooter>
            </Card>
            <Card>
                <CardHeader>
                    <CardTitle>Misc</CardTitle>
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
