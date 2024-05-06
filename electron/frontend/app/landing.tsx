'use client'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { useLocalStorage } from '@/lib/hooks/chat.use-local-storage'
import Home from './home'
import OnboardingModal from '@/components/modals/onboarding-modal'
import useStartSession from '@/lib/services/sessionService/use-start-session'
import { LocalStorageKey } from '@/lib/types'
import SelectProjectDirectoryModal from '@/components/modals/select-project-directory-modal'

export default function Landing({ chatProps }) {
    const searchParams = useSearchParams()
    const chatId = searchParams.get('chat')
    const [hasAcceptedCheckbox, setHasAcceptedCheckbox] =
        useLocalStorage<boolean>(LocalStorageKey.hasAcceptedCheckbox, false)
    const { startSession, sessionStarted, error, loading } = useStartSession()
    const [openProjectModal, setOpenProjectModal] = useState(false)

    // Basically listens for change
    useEffect(() => {
        // Handle when the chatId is 'New', which means the session hasn't been made yet, and we should prompt the select project modal
        if (chatId && chatId === 'New') {
            // window.history.replaceState({}, '', '/')

            // window.location.reload()
            // setOpenProjectModal(true)
            return
        }
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
            <SelectProjectDirectoryModal
                openProjectModal={openProjectModal}
                hideclose
            />
        </>
    )
}
