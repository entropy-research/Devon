
import { useLocalStorage } from '@/lib/hooks/chat.use-local-storage'
import Home, { SessionMachineContext } from './home'
import OnboardingModal from '@/components/modals/onboarding-modal'
import { LocalStorageKey } from '@/lib/types'
import SelectProjectDirectoryModal from '@/components/modals/select-project-directory-modal'
import { useSafeStorage } from './lib/services/safeStorageService'
import { useEffect, useState } from 'react'

export default function Landing({ smHealthCheckDone, setSmHealthCheckDone }: {
    smHealthCheckDone: boolean,
    setSmHealthCheckDone: (value: boolean) => void
}) {
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

    const sessionActorref = SessionMachineContext.useActorRef()
    const state = SessionMachineContext.useSelector(state => state, (a, b) => a.value === b.value)

    if (!smHealthCheckDone && state && !state.matches({ setup: "healthcheck" })) {
        setSmHealthCheckDone(true)
        if (state.context.healthcheckRetry >= 10) {
            alert(`Application failed health check\n\nRetries: ${state.context.healthcheckRetry}\n\nPlease report / find more info on this issue here:\nhttps://github.com/entropy-research/Devon/issues`,)
        }
    }

    return (
        <>
            <Home />

            {smHealthCheckDone && !onboarded && <OnboardingModal
            // initialized={false}
            // setInitialized={() => {}}
            />}
            <div className="dark">
                {smHealthCheckDone && onboarded && <SelectProjectDirectoryModal
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
