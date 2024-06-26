import { useState, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { CardHeader, CardContent, Card } from '@/components/ui/card'
import { useToast } from '@/components/ui/use-toast'
import { useSafeStorage } from '@/lib/services/safeStorageService'
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from '@/components/ui/popover'
import { CircleHelp, Settings, Info } from 'lucide-react'
import SafeStoragePopoverContent from '@/components/modals/safe-storage-popover-content'
import { Skeleton } from '@/components/ui/skeleton'
import { Model } from '@/lib/types'
import { models } from '@/lib/config'
import { Dialog, DialogTrigger, DialogContent } from '@/components/ui/dialog'
import Combobox, { ComboboxItem } from '@/components/ui/combobox'
import { SessionMachineContext } from '@/contexts/session-machine-context'
import FolderPicker from '@/components/ui/folder-picker'

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
    const [open, setOpen] = useState(false)
    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>{trigger}</DialogTrigger>
            <DialogContent className="w-[500px]">
                <General setOpen={setOpen} />
            </DialogContent>
        </Dialog>
    )
}

const General = ({ setOpen }: { setOpen: (val: boolean) => void }) => {
    const { toast } = useToast()
    const [selectedModel, setSelectedModel] = useState(comboboxItems[0])
    // Checking model
    const {
        checkHasEncryptedData,
        getUseModelName,
        deleteData,
        setUseModelName,
        getApiKey,
    } = useSafeStorage()
    const sessionActorref = SessionMachineContext.useActorRef()
    let state = SessionMachineContext.useSelector(state => state)

    const [originalModelName, setOriginalModelName] = useState(
        comboboxItems[0].id
    )
    const [modelHasSavedApiKey, setModelHasSavedApiKey] = useState(false)
    const [folderPath, setFolderPath] = useState('')
    const [initialFolderPath, setInitialFolderPath] = useState<{
        loading: boolean
        value: string | null
    }>({
        loading: true,
        value: null,
    })

    const clearStorageAndResetSession = () => {
        deleteData()
        toast({ title: 'Storage cleared!' })
        sessionActorref.send({ type: 'session.delete' })
    }

    useEffect(() => {
        if (!state?.context?.sessionState?.path) {
            return
        }
        setFolderPath(state.context.sessionState.path)
        if (!initialFolderPath.value) {
            setInitialFolderPath({
                loading: false,
                value: state.context.sessionState.path,
            })
        }
    }, [state?.context?.sessionState?.path])

    useEffect(() => {
        const check = async () => {
            const hasEncryptedData = await checkHasEncryptedData()
            if (hasEncryptedData) {
                const modelName: string = await getUseModelName()
                if (modelName) {
                    const foundModel = models.find(
                        model => model.id === modelName
                    )
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

    const fetchApiKey = useCallback(async () => {
        const res = await getApiKey(selectedModel.id)
        return res
    }, [selectedModel.id])

    function handleUseNewModel() {
        sessionActorref.send({ type: 'session.delete' })
        setUseModelName(selectedModel.id)
        const _key = fetchApiKey()
        sessionActorref.send({
            type: 'session.create',
            payload: {
                path: folderPath,
                agentConfig: {
                    model: selectedModel.id,
                    api_key: _key,
                },
            },
        })
        sessionActorref.on('session.creationComplete', () => {
            sessionActorref.send({
                type: 'session.init',
                payload: {
                    // path: folderPath,
                    agentConfig: {
                        model: selectedModel.id,
                        api_key: _key,
                    },
                },
            })
        })
        setOpen(false)
    }

    function handleChangePath() {
        sessionActorref.send({ type: 'session.delete' })
        setOpen(false)
    }

    // use this when we implement the change directory button
    function handleNewChat() {
        sessionActorref.send({ type: 'session.delete' })
        setUseModelName(selectedModel.id)
        const _key = fetchApiKey()
        sessionActorref.send({
            type: 'session.create',
            payload: {
                path: folderPath,
                agentConfig: {
                    model: selectedModel.id,
                    api_key: _key,
                },
            },
        })
        sessionActorref.on('session.creationComplete', () => {
            sessionActorref.send({
                type: 'session.init',
                payload: {
                    // path: folderPath,
                    agentConfig: {
                        model: selectedModel.id,
                        api_key: _key,
                    },
                },
            })
        })
        setOpen(false)
    }

    return (
        <div className="pt-4 pb-2 px-2 flex flex-col gap-5">
            <Card className="bg-midnight">
                <CardContent className="mt-5 w-full">
                    <p className="text-lg font-semibold mb-4">
                        {`Project directory:`}
                    </p>
                    <FolderPicker
                        folderPath={folderPath}
                        setFolderPath={setFolderPath}
                        showTitle={false}
                        customButton={
                            <Button onClick={handleChangePath}>Change</Button>
                        }
                    />
                    {/* Commenting out for now, just does a refresh instead rn */}
                    {/* {!initialFolderPath.loading && initialFolderPath.value !== folderPath && <Button className="mt-5 w-full" onClick={handleNewChat}>Start new chat</Button>} */}
                </CardContent>
            </Card>
            <Card className="bg-midnight">
                <CardContent>
                    <div className="flex flex-col mt-5 w-full mb-4">
                        <div className="flex items-center justify-between">
                            <p className="text-lg font-semibold">
                                {selectedModel.id !== originalModelName
                                    ? `Set new model: `
                                    : `Current model:`}
                            </p>
                            <div className="flex flex-col">
                                <Combobox
                                    items={comboboxItems}
                                    itemType="model"
                                    selectedItem={selectedModel}
                                    setSelectedItem={setSelectedModel}
                                />
                            </div>
                        </div>
                        {selectedModel.value !== 'claude-3-5-sonnet' && (
                            <span className="text-sm text-green-500 mt-2 flex gap-1 items-center">
                                <Info className="w-4 h-4"/>
                                Note: For best results use Claude 3.5 Sonnet (it's better at coding!)
                            </span>
                        )}
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
                        {selectedModel.id !== originalModelName &&
                            modelHasSavedApiKey && (
                                <Button onClick={handleUseNewModel}>
                                    {'Use this model'}
                                </Button>
                            )}
                    </div>
                    <APIKeyComponent
                        key={selectedModel.id}
                        model={selectedModel}
                        sessionActorref={sessionActorref}
                        setModelHasSavedApiKey={setModelHasSavedApiKey}
                    />
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
                            <PopoverContent
                                side="top"
                                className="bg-night w-fit p-2 px-3"
                            >
                                Clears your keys from Electron Safe Storage and
                                clears the session
                            </PopoverContent>
                        </Popover>
                    </div>
                </CardHeader>
                <CardContent>
                    <Button
                        className="w-fit"
                        onClick={clearStorageAndResetSession}
                    >
                        Clear Storage
                    </Button>
                </CardContent>
            </Card>
        </div>
    )
}

const APIKeyComponent = ({
    model,
    sessionActorref,
    setModelHasSavedApiKey,
}: {
    model: Model
    sessionActorref: any
    setModelHasSavedApiKey: (value: boolean) => void
}) => {
    const { addApiKey, getApiKey, removeApiKey, setUseModelName } =
        useSafeStorage()
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
