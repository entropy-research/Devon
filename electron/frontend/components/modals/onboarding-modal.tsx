'use client'

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
import Combobox from '@/components/ui/combobox'

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

const models = [
    {
        value: 'gpt4-o',
        label: 'GPT4-o',
        company: 'OpenAI',
    },
    {
        value: 'claude-opus',
        label: 'Claude Opus',
        company: 'Anthropic',
    },
    {
        value: 'llama-3-70b',
        label: 'Llama 3.70b',
        company: 'Groq',
    },
]

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
    const [selectedModel, setSelectedModel] = useState<{
        value: string
        label: string
        company: string
    }>(models[0])

    const { saveData, deleteData, checkHasEncryptedData } = useSafeStorage()
    const [hasEncryptedData, setHasEncryptedData] = useState(false)

    useEffect(() => {
        checkHasEncryptedData().then(setHasEncryptedData)
    }, [checkHasEncryptedData])

    function afterSubmit() {
        saveData(apiKey) // Store the api key
        setInitialized(true)
    }

    const handleCheckboxChange = () => {
        setIsChecked(!isChecked)
    }

    const handleApiKeyInputChange = (
        e: React.ChangeEvent<HTMLInputElement>
    ) => {
        setApiKey(e.target.value)
    }

    function validateFields() {
        if (!isChecked) return false
        return (apiKey || hasEncryptedData) !== '' && folderPath !== ''
    }

    return (
        <Suspense fallback={<></>}>
            <Dialog open={!initialized} onOpenChange={setInitialized}>
                <DialogContent hideclose={true.toString()}>
                    <div className="flex flex-col items-center justify-center my-8 mx-8">
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
                            <label className="ml-2">
                                I understand that this is not associated with
                                Cognition Labs&apos;s Devin
                            </label>
                        </div>
                        <DisabledWrapper
                            disabled={!isChecked}
                            className="mt-10"
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
                                <div className="flex items-center mb-4 gap-3">
                                    <p className="text-lg font-semibold">
                                        {`Choose your model:`}
                                    </p>
                                    <Combobox
                                        items={models}
                                        itemType="model"
                                        selectedItem={selectedModel}
                                        setSelectedItem={setSelectedModel}
                                    />
                                </div>

                                <div className="flex gap-1 items-center mb-4">
                                    {/* <Key size={20} className="mb-1" /> */}
                                    <p className="text-xl font-bold">
                                        {`${selectedModel.company} API Key`}
                                    </p>
                                    <Popover>
                                        <PopoverTrigger className="ml-1">
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
                                <Input
                                    className="w-full"
                                    type="password"
                                    value={
                                        hasEncryptedData
                                            ? '***************'
                                            : apiKey
                                    }
                                    onChange={handleApiKeyInputChange}
                                    disabled={!isChecked || hasEncryptedData}
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
