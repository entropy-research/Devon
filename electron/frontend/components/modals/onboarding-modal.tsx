import {
    useState,
    Suspense,
    lazy,
    Dispatch,
    SetStateAction,
    useEffect,
} from 'react'
import { CircleHelp } from 'lucide-react'
import { Checkbox } from '@/components/ui/checkbox'
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
import SafeStoragePopoverContent from '@/components/safe-storage-popover-content'
import Combobox, { ComboboxItem } from '@/components/ui/combobox'
import { Model } from '@/lib/types'
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
    initialized,
    setInitialized,
}: {
    initialized: boolean
    setInitialized: Dispatch<SetStateAction<boolean>>
}) => {
    const [folderPath, setFolderPath] = useState('')
    const [isChecked, setIsChecked] = useState(false)
    const [apiKey, setApiKey] = useState('')
    const [selectedModel, setSelectedModel] = useState(comboboxItems[0])
    const { addApiKey, getApiKey } = useSafeStorage()
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

    const handleCheckboxChange = () => {
        setIsChecked(!isChecked)
    }

    const handleApiKeyInputChange = (
        e: React.ChangeEvent<HTMLInputElement>
    ) => {
        setApiKey(e.target.value)
    }

    function afterSubmit() {
        const handleSaveApiKey = async () => {
            await addApiKey(selectedModel.value, apiKey)
            setIsKeySaved(true)
        }
        handleSaveApiKey() // Store the api key
        setInitialized(true)
    }

    function validateFields() {
        if (!isChecked) return false
        return (apiKey !== '' || isKeySaved) && folderPath !== ''
    }

    return (
        <Suspense fallback={<></>}>
            <Dialog open={!initialized} onOpenChange={setInitialized}>
                <DialogContent hideclose="true">
                    <div className="flex flex-col items-center justify-center my-8 mx-8 max-w-md">
                        <h1 className="text-3xl font-bold">
                            Welcome to Devon!
                        </h1>
                        <p className="text-md mt-3">Devon, not Devin</p>
                        <div className="flex mt-6 gap-1">
                            <Checkbox
                                className="mt-1"
                                checked={isChecked}
                                onClick={handleCheckboxChange}
                            />
                        </div>
                        <DisabledWrapper
                            disabled={!isChecked}
                            className="mt-10 w-full"
                        >
                            <SelectProjectDirectoryComponent
                                folderPath={folderPath}
                                setFolderPath={setFolderPath}
                                disabled={!isChecked}
                            />
                        </DisabledWrapper>
                        <DisabledWrapper
                            disabled={!isChecked}
                            className="w-full"
                        >
                            <div className="flex flex-col mt-10 w-full">
                                <div className="flex items-center justify-between mb-4 gap-3">
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

                                <div className="flex gap-1 items-center mb-4">
                                    <p className="text-xl font-bold">
                                        {`${selectedModel.company} API Key`}
                                    </p>
                                    <Popover>
                                        <PopoverTrigger className="ml-1">
                                            <CircleHelp size={20} />
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
                                {isKeySaved ? (
                                    <Input
                                        className="w-full"
                                        type="password"
                                        value="**********************"
                                        disabled
                                    />
                                ) : (
                                    <Input
                                        className="w-full"
                                        type="password"
                                        value={apiKey}
                                        onChange={handleApiKeyInputChange}
                                        disabled={!isChecked}
                                    />
                                )}
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
