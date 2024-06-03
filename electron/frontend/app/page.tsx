'use client'

import Landing from './landing'
import { QueryClient, QueryClientProvider } from 'react-query'

const queryClient = new QueryClient()

export default function IndexPage() {
    return (
        <QueryClientProvider client={queryClient}>
            <Landing />
        </QueryClientProvider>
    )
}
