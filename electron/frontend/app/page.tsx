'use client'

import Landing from './landing'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BackendUrlProvider } from '../contexts/BackendUrlContext'
import { StateMachineProvider } from '@/lib/services/stateMachineService/stateMachineContext'

const queryClient = new QueryClient()

export default function IndexPage() {
    return (
        <QueryClientProvider client={queryClient}>
            <BackendUrlProvider>
                <StateMachineProvider>
                    {/* <AI initialAIState={{ chatId: chat.id, messages: chat.messages }}> */}
                    <Landing />
                    {/* </AI> */}
                </StateMachineProvider>
            </BackendUrlProvider>
        </QueryClientProvider>
    )
}
