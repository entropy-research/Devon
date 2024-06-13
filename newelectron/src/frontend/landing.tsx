
import Home, { SessionMachineContext } from './home'
import OnboardingModal from '@/components/modals/onboarding-modal'
import SelectProjectDirectoryModal from '@/components/modals/select-project-directory-modal'
import { useSafeStorage } from './lib/services/safeStorageService'
import { useEffect, useState } from 'react'

export default function Landing({ smHealthCheckDone, setSmHealthCheckDone }: {
    smHealthCheckDone: boolean,
    setSmHealthCheckDone: (value: boolean) => void
}) {
    const { checkHasEncryptedData, getUseModelName } = useSafeStorage()
    const [modelName, setModelName] = useState('')
    const [onboarded, setOnboarded] = useState(false)

    useEffect(() => {
        const check = async () => {
            const hasEncryptedData = await checkHasEncryptedData()
            console.log('hasEncryptedData', hasEncryptedData)
            if (hasEncryptedData) {
                const modelName = await getUseModelName()
                setModelName(modelName)
                console.log('modelName', modelName)
            }
        }
        check()
    }, [checkHasEncryptedData])

    const sessionActorref = SessionMachineContext.useActorRef()
    const state = SessionMachineContext.useSelector(state => state, (a, b) => a.value === b.value)

    function afterOnboard(apiKey: string, _modelName: string, folderPath: string) {

        console.log("API KEY", apiKey, _modelName)
        sessionActorref.send({
            type: 'session.create', payload: {
                path: folderPath,
                agentConfig: {
                    model: _modelName,
                    api_key: apiKey
                }
            }
        })
        sessionActorref.on("session.creationComplete", () => {
            sessionActorref.send({
                type: 'session.init', payload: {
                    // path: folderPath,
                    agentConfig: {
                        model: _modelName,
                        api_key: apiKey
                    }
                }
            })
        })
    }

    if (!smHealthCheckDone && state && !state.matches({ setup: "healthcheck" })) {
        setSmHealthCheckDone(true)
        if (state.context.healthcheckRetry >= 10) {
            alert(`Application failed health check\n\nRetries: ${state.context.healthcheckRetry}\n\nPlease report / find more info on this issue here:\nhttps://github.com/entropy-research/Devon/issues`,)
        }
    }


    return (
        <>
            <Home />

            {smHealthCheckDone && !modelName && <OnboardingModal
                setModelName={setModelName}
                setOnboarded={setOnboarded}
                afterOnboard={afterOnboard}
            />}
            <div className="dark">
                {smHealthCheckDone && !onboarded && modelName && <SelectProjectDirectoryModal
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
