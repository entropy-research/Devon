
import { useLocalStorage } from '@/lib/hooks/chat.use-local-storage'
import Home, { SessionMachineContext } from './home'
import OnboardingModal from '@/components/modals/onboarding-modal'
import { LocalStorageKey } from '@/lib/types'
import SelectProjectDirectoryModal from '@/components/modals/select-project-directory-modal'
import { useSafeStorage } from './lib/services/safeStorageService'
import { useEffect, useState } from 'react'

export default function Landing() {
    // const [hasAcceptedCheckbox, setHasAcceptedCheckbox] =
    //     useLocalStorage<boolean>(LocalStorageKey.hasAcceptedCheckbox, false)

    // const [hasAcceptedCheckbox, setHasAcceptedCheckbox] = useState(false)

    const { checkHasEncryptedData, getUseModelName } = useSafeStorage()
    const [onboarded, setOnboarded] = useState(false)
    const [modelName, setModelName] = useState('')

    useEffect(() => {
        const check = async () => {
            const hasEncryptedData = await checkHasEncryptedData()
            console.log('hasEncryptedData', hasEncryptedData)
            if (hasEncryptedData) {
                const modelName = await getUseModelName()
                setModelName(modelName)
                console.log('modelName', modelName)
                if (modelName) {
                    setOnboarded(true)
                    return
                }
            }
            setOnboarded(false)
        }
        check()
    }, [checkHasEncryptedData])
    console.log('onboarded', onboarded)
    const sessionActorref = SessionMachineContext.useActorRef()
    const state = SessionMachineContext.useSelector(state => state, (a, b) => a.value === b.value)
    return (
        <>
            <Home />

            {!onboarded && <OnboardingModal
            // initialized={false}
            // setInitialized={() => {}}
            />}
            <div className="dark">
                {onboarded && <SelectProjectDirectoryModal
                    openProjectModal={!state.can({ type: 'session.toggle' }) && !state.matches('resetting')}
                    hideclose
                    sessionActorref={sessionActorref}
                    state={state}
                    model={modelName}
                />
                }
            </div>
        </>
    )
}
