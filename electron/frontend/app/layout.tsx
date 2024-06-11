"use client"
// import type { Metadata } from 'next'
import { DM_Sans } from 'next/font/google'
import { Toaster } from '@/components/ui/toaster'
import HeaderSidebar from '@/components/header-sidebar'
import { BackendUrlProvider } from '../contexts/BackendUrlContext'

import './globals.css'
import { useEffect, useState } from 'react'

// const inter = Inter({ subsets: ['latin'] })
const dmSans = DM_Sans({ subsets: ['latin'] })

// Can't do this with bc provider needs 'use client'
// export const metadata: Metadata = {
//     title: 'Devon',
//     description: 'Open-Source AI Software Engineer',
// }

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode
}>) {
    return (
        <html lang="en" className="dark h-full">
            <body className={`${dmSans.className} flex h-full flex-col`}>
                <div className="flex w-full h-full overflow-hidden">
                    <div className="relative w-full overflow-hidden bg-day transition-colors duration-200 dark:bg-night flex">
                        <BackendUrlProvider>
                            <HeaderSidebar />
                            <main className="mt-[54px] flex flex-row w-full">
                                {children}
                            </main>
                        </BackendUrlProvider>
                    </div>
                </div>
                <Toaster />
            </body>
        </html>
    )
}
