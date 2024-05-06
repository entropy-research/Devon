'use client'
import { useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { useLocalStorage } from '@/lib/hooks/chat.use-local-storage'
import Home from './home'
import OnboardingModal from '@/components/modals/onboarding-modal'
import useStartSession from '@/lib/services/sessionService/use-start-session'

export default function Landing({ chatProps }) {
    const searchParams = useSearchParams()
    const chatId = searchParams.get('chat')
    const [hasAcceptedCheckbox, setHasAcceptedCheckbox] = useLocalStorage(
        'hasAcceptedCheckbox',
        false
    )
    const { startSession, sessionStarted, error, loading } = useStartSession()

    // Basically listens for change
    useEffect(() => {
        if (loading) {
            return
        }
        if (error) {
            console.error('Error starting session:', error)
        }
        // Check if session already started
        if (sessionStarted) {
            chatProps.id = chatId
            return
        }
        // If not, start it
        if (!chatId) {
            return
        }
        startSession(chatId)
        chatProps.id = chatId
    }, [loading, chatId, sessionStarted])

    return (
        <>
            <Home chatProps={chatProps} />
            <OnboardingModal
                initialized={hasAcceptedCheckbox}
                setInitialized={setHasAcceptedCheckbox}
            />
        </>
    )
}
