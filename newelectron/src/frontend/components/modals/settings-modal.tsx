import { useState, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
    CardHeader,
    CardContent,
    Card,
} from '@/components/ui/card'
import { useToast } from '@/components/ui/use-toast'
import { useSafeStorage } from '@/lib/services/safeStorageService'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { CircleHelp, Settings } from 'lucide-react'
import SafeStoragePopoverContent from '@/components/safe-storage-popover-content'
import { Skeleton } from '@/components/ui/skeleton'
import { Model } from '@/lib/types'
import { models } from '@/lib/config'
import { Dialog, DialogTrigger, DialogContent } from '@/components/ui/dialog'
import Combobox, { ComboboxItem } from '@/components/ui/combobox'
import { SessionMachineContext } from '@/home'


type ExtendedComboboxItem = Model & ComboboxItem & { company: string }

const comboboxItems: ExtendedComboboxItem[] = models
    .filter(model => !model.comingSoon)
    .map(model => ({
        ...model,
        value: model.id,
        label: model.name,
        company: model.company,
    }))

const SettingsModal = ({ trigger }: { trigger: JSX.Element }) => {
    return (
        <Dialog>
            <DialogTrigger asChild>
                {trigger}
            </DialogTrigger>
            <DialogContent className="w-[500px]">
                <General />
            </DialogContent>
        </Dialog>
    )
}

const General = () => {
    const { toast } = useToast()
    const [selectedModel, setSelectedModel] = useState(comboboxItems[0])
    // Checking model
    const { checkHasEncryptedData, getUseModelName, deleteData } = useSafeStorage()
    const sessionActorref = SessionMachineContext.useActorRef()
    const [originalModelName, setOriginalModelName] = useState(comboboxItems[0].id)
    const [modelHasSavedApiKey, setModelHasSavedApiKey] = useState(false)

    const clearStorageAndResetSession = () => {
        deleteData()
        toast({ title: 'Storage cleared!' })
        sessionActorref.send({ type: 'session.delete' })
    }

    useEffect(() => {
        const check = async () => {
            const hasEncryptedData = await checkHasEncryptedData()
            if (hasEncryptedData) {
                const modelName: string = await getUseModelName()
                if (modelName) {
                    const foundModel = models.find(model => model.id === modelName)
                    if (foundModel) {
                        const extendedComboboxModel = {
                            ...foundModel,
                            value: foundModel.id,
                            label: foundModel.name,
                            company: foundModel.company,
                        }
                        setSelectedModel(extendedComboboxModel)
                        setOriginalModelName(modelName)
                    }
                }
            }
        }
        check()
    }, [])

    function handleUseNewModel() {
        sessionActorref.send({ type: 'session.delete' })
    }

    return (
        <div className="pt-4 pb-2 px-2 flex flex-col gap-5">
            <Card className="bg-midnight">
                <CardContent>
                    <div className="flex flex-col mt-5 w-full">
                        <div className="flex items-center justify-between mb-4 gap-3">
                            <p className="text-lg font-semibold">
                                {selectedModel.id !== originalModelName ? `Set new model: ` : `Current model:`}
                            </p>
                            <div className="flex gap-3">
                                <Combobox
                                    items={comboboxItems}
                                    itemType="model"
                                    selectedItem={selectedModel}
                                    setSelectedItem={setSelectedModel}
                                />
                            </div>
                        </div>
                    </div>
                    <div className="flex justify-between w-full">
                        <div className="flex gap-1 items-center mb-4">
                            <p className="text-xl font-bold">
                                {`${selectedModel.company} API Key`}
                            </p>
                            <Popover>
                                <PopoverTrigger className="ml-[2px]">
                                    <CircleHelp size={14} />
                                </PopoverTrigger>
                                <SafeStoragePopoverContent />
                            </Popover>

                        </div>
                        {selectedModel.id !== originalModelName && modelHasSavedApiKey && <Button
                        onClick={handleUseNewModel}
                        >
                            {'Use this model'}
                        </Button>}
                    </div>
                    <APIKeyComponent key={selectedModel.id} model={selectedModel} sessionActorref={sessionActorref} setModelHasSavedApiKey={setModelHasSavedApiKey} />
                    {/* <Input
                        className="w-full"
                        type="password"
                        value={123}
                        // onChange={handleApiKeyInputChange}
                        // disabled={!isChecked || isKeySaved}
                    /> */}
                </CardContent>
            </Card>
            {/* <Card className="bg-midnight">
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
            </Card> */}
            <Card className="bg-midnight">
                <CardHeader>
                    <div className="flex gap-1 items-center">
                        <h2 className="text-lg font-semibold">Miscellaneous</h2>
                        <Popover>
                            <PopoverTrigger className="ml-[2px]">
                                <CircleHelp size={14} />
                            </PopoverTrigger>
                            <PopoverContent side='top' className="bg-night w-fit p-2 px-3">Clears your keys from Electron Safe Storage and clears the session</PopoverContent>
                        </Popover>
                    </div>
                </CardHeader>
                <CardContent>
                    <Button className="w-fit" onClick={clearStorageAndResetSession}>
                        Clear Storage
                    </Button>
                </CardContent>
            </Card>
        </div>
    )
}

const APIKeyComponent = ({ model, sessionActorref, setModelHasSavedApiKey }: { model: Model, sessionActorref: any, setModelHasSavedApiKey: (value: boolean) => void }) => {
    const { addApiKey, getApiKey, removeApiKey, setUseModelName } = useSafeStorage()
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
            setModelHasSavedApiKey(true)
        } else {
            setIsKeyStored(false)
            setModelHasSavedApiKey(false)

        }
        setIsLoading(false)
    }, [model.id])

    useEffect(() => {
        fetchApiKey()
    }, [])

    const handleSave = async () => {
        setIsSaving(true)
        await addApiKey(model.id, key)
        // Update the model as well
        await setUseModelName(model.id)
        setIsKeyStored(true)
        setIsSaving(false)
        // Right now even if the current session isn't using the model, it will still reset the session once key deleted
        sessionActorref.send({ type: 'session.delete' })
    }

    const handleDelete = async () => {
        setIsSaving(true)
        await removeApiKey(model.id)
        setIsKeyStored(false)
        setKey('')
        setIsSaving(false)
        // Right now even if the current session isn't using the model, it will still reset the session once key deleted
        sessionActorref.send({ type: 'session.delete' })
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
                        variant="outline-thin"
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
                            {/* {isSaving ? 'Saving...' : 'Save'} */}
                            {isSaving ? 'Saving...' : 'Save and use'}
                        </Button>
                    )}
                </div>
            )}
        </div>
    )
}

export default SettingsModal
