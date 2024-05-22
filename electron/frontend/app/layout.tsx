import type { Metadata } from 'next'
import { DM_Sans } from 'next/font/google'
import { Toaster } from '@/components/ui/toaster'
import HeaderSidebar from './header-sidebar'

import './globals.css'

// const inter = Inter({ subsets: ['latin'] })
const dmSans = DM_Sans({ subsets: ['latin'] })

export const metadata: Metadata = {
    title: 'Devon',
    description: 'Open-Source AI Software Engineer',
}

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode
}>) {
    return (
        <html lang="en" className="dark h-full">
            <body className={`${dmSans.className} flex h-full flex-col`}>
                <div className="flex w-full h-full overflow-hidden">
                    <div className="relative w-full overflow-hidden bg-day transition-colors duration-200 dark:bg-night md:flex">
                        <HeaderSidebar />
                        <main className="mt-[54px] flex flex-row w-full">
                            {children}
                        </main>
                    </div>
                </div>
                <Toaster />
            </body>
        </html>
    )
}
