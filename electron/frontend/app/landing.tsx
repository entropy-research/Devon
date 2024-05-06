'use client'
import { useState, useEffect } from 'react'
// Landing page to prompt user for project directory and API key(s)
// import { fromEvent } from 'file-selector'
import { useRouter, usePathname, useSearchParams } from 'next/navigation'
// import { useRouter } from 'next/router';
import FolderPicker from '@/components/ui/folder-picker'
import { Button } from '@/components/ui/button'
import { useLocalStorage } from '@/lib/hooks/chat.use-local-storage'
import { nanoid } from '@/lib/chat.utils'
import Home from './home'
import OnboardingModal from '@/components/modals/onboarding-modal'
import useStartSession from '@/lib/services/sessionService/use-start-session'
// import useFetchSessionEvents from '@/lib/services/sessionService/use-fetch-session-events'
import useCreateSession from '@/lib/services/sessionService/use-create-session'


export default function Landing({ chatProps }) {
    const searchParams = useSearchParams()

    const chatId = searchParams.get('chat')
    const [folderPath, setFolderPath] = useState('')
    // const [_, setChatId] = useLocalStorage('chatId', chatId)
    const [hasAcceptedCheckbox, setHasAcceptedCheckbox] = useLocalStorage(
        'hasAcceptedCheckbox',
        false
    )
    // const [initialized, setInitialized] = useState(true)
    const { startSession, sessionStarted, error, loading } = useStartSession()
    const { createSession, sessionId, loading: createSessionLoading, error: createSessionError } = useCreateSession()

    // const { data: events, isLoading, isError, error } = useFetchSessionEvents(sessionId);

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
