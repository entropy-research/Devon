import { useEffect, useState } from 'react'
import Landing from './landing'
import { useBackendUrl } from '@/contexts/BackendUrlContext'
import { SessionContextProviderComponent } from './home'
import AtomLoader from '@/components/ui/atom-loader/atom-loader'

export default function IndexPage() {
    const { backendUrl } = useBackendUrl()

    const [sessionMachineProps, setSessionMachineProps] = useState<{
        host: string
        name: string
    } | null>(null)
    const [smHealthCheckDone, setSmHealthCheckDone] = useState(false)

    useEffect(() => {
        if (backendUrl) {
            setSessionMachineProps({ host: backendUrl, name: 'UI' })
        }
    }, [backendUrl])

    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        // Ensure the loader is displayed for at least 3 seconds
        const minimumLoadingDuration = 1500
        const timer = setTimeout(() => {
            setIsLoading(false)
        }, minimumLoadingDuration)

        return () => clearTimeout(timer)
    }, [])

    return (
        <>
            {sessionMachineProps && !isLoading && (
                <SessionContextProviderComponent
                    sessionMachineProps={sessionMachineProps}
                >
                    <Landing
                        smHealthCheckDone={smHealthCheckDone}
                        setSmHealthCheckDone={setSmHealthCheckDone}
                    />
                </SessionContextProviderComponent>
            )}
            {!sessionMachineProps ||
                isLoading ||
                (!smHealthCheckDone && (
                    <div className="absolute top-0 left-0 w-full h-full bg-night z-50">
                        <div className="fixed left-[50%] top-[50%] grid translate-x-[-50%] translate-y-[-50%]">
                            <div className="flex items-center justify-center flex-col gap-10">
                                <AtomLoader size="lg" />
                                <p className="text-2xl">{`Devon's cleaning up his desk...`}</p>
                            </div>
                        </div>
                    </div>
                ))}
        </>
    )
}
