import { DM_Sans } from 'next/font/google'
import { Toaster } from '@/components/ui/toaster'
import { BackendUrlProvider } from '../contexts/BackendUrlContext'


const dmSans = DM_Sans({ subsets: ['latin'] })
import './globals.css'

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
