'use client'
import { useState } from 'react'
// Landing page to prompt user for project directory and API key(s)
// import { fromEvent } from 'file-selector'
import { useRouter } from 'next/navigation'
import FolderPicker from '@/components/ui/folder-picker'
import { Button } from '@/components/ui/button'
import { useLocalStorage } from '@/lib/hooks/chat.use-local-storage'
import { nanoid } from '@/lib/chat.utils'
import Home from './home'
import OnboardingModal from '@/components/onboarding-modal'

export default function Landing({ chatProps }) {
    const router = useRouter()
    const [folderPath, setFolderPath] = useState('')
    // const [_, setChatId] = useLocalStorage('chatId', '1')
    const [initialized, setInitialized] = useState(true)

    function handleStartChat() {
        // setChatId(nanoid())
        setInitialized(true)
    }

    return (
        <>
            <Home chatProps={chatProps} />
            <OnboardingModal
                initialized={initialized}
                setInitialized={setInitialized}
            />
        </>
    )
}
