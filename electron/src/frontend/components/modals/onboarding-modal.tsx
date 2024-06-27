import { useState, Suspense, lazy, useEffect } from 'react'
import { CircleHelp, Info } from 'lucide-react'
import { Input } from '@/components/ui/input'
import DisabledWrapper from '@/components/ui/disabled-wrapper'
import {
    SelectProjectDirectoryComponent,
    StartChatButton,
} from '@/components/modals/select-project-directory-modal'
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from '@/components/ui/popover'
import { useSafeStorage } from '@/lib/services/safeStorageService'
import SafeStoragePopoverContent from '@/components/modals/safe-storage-popover-content'
import Combobox, { ComboboxItem } from '@/components/ui/combobox'
import { models } from '@/lib/config'

const Dialog = lazy(() =>
    import('@/components/ui/dialog').then(module => ({
        default: module.Dialog,
    }))
)
const DialogContent = lazy(() =>
    import('@/components/ui/dialog').then(module => ({
        default: module.DialogContent,
    }))
)

type ExtendedComboboxItem = ComboboxItem & { company: string }

const comboboxItems: ExtendedComboboxItem[] = models
    .filter(model => !model.comingSoon)
    .map(model => ({
        value: model.id,
        label: model.name,
        company: model.company,
    }))

const OnboardingModal = ({
    setModelName,
    setOnboarded,
    afterOnboard,
}: {
    setModelName: (value: string) => void
    setOnboarded: (value: boolean) => void
    afterOnboard: (
        apiKey: string,
        modelName: string,
        folderPath: string
    ) => void
}) => {
    const [folderPath, setFolderPath] = useState('')
    const [apiKey, setApiKey] = useState('')
    const [selectedModel, setSelectedModel] = useState(comboboxItems[0])
    const { addApiKey, getApiKey, setUseModelName } = useSafeStorage()
    const [isKeySaved, setIsKeySaved] = useState(false)

    useEffect(() => {
        const fetchApiKey = async () => {
            const res = await getApiKey(selectedModel.value)
            // If it's already entered, don't let user edit
            if (res) {
                setApiKey(res)
                setIsKeySaved(true)
            } else {
                setApiKey('')
                setIsKeySaved(false)
            }
        }
        fetchApiKey()
    }, [selectedModel])

    const handleApiKeyInputChange = (
        e: React.ChangeEvent<HTMLInputElement>
    ) => {
        setApiKey(e.target.value)
    }

    function afterSubmit() {
        const handleSaveApiKey = async () => {
            await addApiKey(selectedModel.value, apiKey, false)
            setIsKeySaved(true)
            await setUseModelName(selectedModel.value, false)
        }
        handleSaveApiKey() // Store the api key
        afterOnboard(apiKey, selectedModel.value, folderPath)
        setOnboarded(true) // Makes sure the other modal doesn't show up
        setModelName(selectedModel.value) // Closes the modal
    }

    function validateFields() {
        // if (!isChecked) return false
        return (apiKey !== '' || isKeySaved) && folderPath !== ''
    }

    return (
        <Suspense fallback={<></>}>
            <Dialog open={true}>
                <DialogContent hideclose={true.toString()} className="w-[500px]">
                    <div className="flex flex-col items-center justify-center my-8 mx-8">
                        <h1 className="text-3xl font-bold">
                            Welcome to Devon!
                        </h1>
                        <DisabledWrapper
                            disabled={false}
                            className="mt-10 w-full"
                        >
                            <SelectProjectDirectoryComponent
                                folderPath={folderPath}
                                setFolderPath={setFolderPath}
                            />
                        </DisabledWrapper>
                        <DisabledWrapper disabled={false} className="w-full">
                            <div className="flex flex-col mt-10 w-full">
                                <div className="flex flex-col mb-5">
                                    <div className="flex items-center justify-between gap-3">
                                        <p className="text-lg font-semibold">
                                            {`Choose your model:`}
                                        </p>
                                        <Combobox
                                            items={comboboxItems}
                                            itemType="model"
                                            selectedItem={selectedModel}
                                            setSelectedItem={setSelectedModel}
                                        />
                                    </div>
                                    {selectedModel.value !==
                                        'claude-3-5-sonnet' && (
                                        <span className="text-sm text-green-500 mt-2 flex gap-1 items-center">
                                            <Info className="w-4 h-4" />
                                            Note: For best results use Claude
                                            3.5 Sonnet (it's better at coding!)
                                        </span>
                                    )}
                                </div>

                                <div className="flex gap-1 items-center mb-4">
                                    <p className="text-lg font-bold">
                                        {`${selectedModel.company} API Key`}
                                    </p>
                                    <Popover>
                                        <PopoverTrigger className="ml-[2px]">
                                            <CircleHelp size={14} />
                                        </PopoverTrigger>
                                        {isKeySaved ? (
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
                                <Input
                                    className="w-full"
                                    type="password"
                                    value={apiKey}
                                    onChange={handleApiKeyInputChange}
                                    disabled={isKeySaved}
                                />
                            </div>
                        </DisabledWrapper>
                        <StartChatButton
                            disabled={!validateFields()}
                            onClick={afterSubmit}
                            folderPath={folderPath}
                        />
                    </div>
                </DialogContent>
            </Dialog>
        </Suspense>
    )
}

export default OnboardingModal
