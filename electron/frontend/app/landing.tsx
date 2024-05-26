'use client'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { useLocalStorage } from '@/lib/hooks/chat.use-local-storage'
import Home from './home'
import OnboardingModal from '@/components/modals/onboarding-modal'
import useStartSession from '@/lib/services/sessionService/use-start-session'
import { LocalStorageKey } from '@/lib/types'
import SelectProjectDirectoryModal from '@/components/modals/select-project-directory-modal'
import { StateMachineProvider, useSessionService, useStartSessionContext } from '@/lib/services/stateMachineService/stateMachineContext'
// import { useSessionService } from '@/lib/services/stateMachineService/stateMachineContext'

export default function Landing({ chatProps }) {
    const searchParams = useSearchParams()
    const [hasAcceptedCheckbox, setHasAcceptedCheckbox] =
        useLocalStorage<boolean>(LocalStorageKey.hasAcceptedCheckbox, false)
    const [openProjectModal, setOpenProjectModal] = useState(false)
    // const { startSession, sessionStarted, error, loading } = useStartSession()
    // const [sessionStarted, setSessionStarted] = useState(false)
    // const [port] = useState(10001);
    // const sessionService = useSessionService()
    const startSession = useStartSessionContext();

    // Basically listens for change
    useEffect(() => {
        console.log('sessionService hook')
        const chatId = searchParams.get('chat')
        // Handle when the chatId is 'New', which means the session hasn't been made yet, and we should prompt the select project modal
        if (chatId && chatId === 'New') {
            return
        }

        if (!chatId) {
            return
        }

        startSession(10001, 'NEWCHAT', '/Users/josh/Documents/cs/entropy/examples');
        // Check if session already started
        // if (sessionService.state.matches('running')) {
        //     chatProps.id = chatId;
        //     return;
        // }
        // sessionService.send({
        //     type: 'xstate.init',
        //     input: { port: 3000, name: chatId, path: process.cwd() },
        // });
        // setSessionStarted(true)
        chatProps.id = chatId
    }, [startSession, searchParams, chatProps])

    useEffect(() => {
        const chatId = searchParams.get('chat')
        if (chatId) return
        if (hasAcceptedCheckbox) {
            setOpenProjectModal(true)
            window.history.replaceState({}, '', '/?chat=New')
        }
    }, [hasAcceptedCheckbox, searchParams])

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
