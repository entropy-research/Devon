'use client'

import { useState, Suspense, lazy, Dispatch, SetStateAction } from 'react'
// import { Key } from 'lucide-react'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import DisabledWrapper from '@/components/ui/disabled-wrapper'
import {
    SelectProjectDirectoryComponent,
    StartChatButton,
} from '@/components/modals/select-project-directory-modal'

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

    function afterSubmit() {
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
        return apiKey !== '' && folderPath !== ''
    }

    return (
        <Suspense fallback={<div>Loading...</div>}>
            <Dialog open={!initialized} onOpenChange={setInitialized}>
                <DialogContent hideclose={true.toString()}>
                    <div className="flex flex-col items-center justify-center my-8 mx-8">
                        <h1 className="text-4xl font-bold">
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
                                <div className="flex gap-1 items-center mb-4">
                                    {/* <Key size={20} className="mb-1" /> */}
                                    <p className="text-xl font-bold">
                                        Anthropic API Key
                                    </p>
                                </div>
                                <Input
                                    className="w-full"
                                    type="password"
                                    value={apiKey}
                                    onChange={handleApiKeyInputChange}
                                    disabled={!isChecked}
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
