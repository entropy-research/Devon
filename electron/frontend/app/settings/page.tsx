'use client'
import Link from 'next/link'
import General from './settings-tabs/general'
import { useComingSoonToast } from '@/components/ui/use-toast'

export default function Page() {
    const toast = useComingSoonToast()
    return (
        <div className="h-screen w-full flex flex-col pb-5 px-[1rem] overflow-hidden">
            <div className="flex flex-1 flex-row gap-4 px-4 pb-4 md:gap-8 md:pl-10 md:pr-0 justify-start overflow-hidden h-full">
                <div className="h-full flex flex-col">
                    <div className="grid w-full max-w-6xl gap-2 mb-4">
                        <h1 className="text-3xl font-semibold mt-4">
                            Settings
                        </h1>
                    </div>
                    <nav className="flex flex-col gap-4 text-sm text-muted-foreground">
                        <Link
                            className="text-lg font-semibold text-primary"
                            href="#"
                        >
                            General
                        </Link>
                        <Link
                            className="text-lg font-semibold text-neutral-500"
                            href="#"
                            onClick={toast}
                        >
                            Advanced
                        </Link>
                    </nav>
                </div>
                <div className="h-full w-full overflow-y-auto px-2">
                    <General />
                </div>
            </div>
        </div>
    )
}
