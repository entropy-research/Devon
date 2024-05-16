'use client'
import Link from 'next/link'
import General from './settings-tabs/general'
import { useComingSoonToast } from '@/components/ui/use-toast'

export default function Page() {
    const toast = useComingSoonToast()
    return (
        <div className="dark:bg-batman rounded-lg h-full w-full flex flex-col py-5 px-[2rem]">
            <div className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-10 justify-start">
                <div className="grid w-full max-w-6xl gap-2">
                    <h1 className="text-3xl font-semibold">Settings</h1>
                </div>
                <div className="grid w-full max-w-6xl items-start gap-6 md:grid-cols-[180px_1fr] lg:grid-cols-[250px_1fr]">
                    <nav className="grid gap-4 text-sm text-muted-foreground">
                        <Link
                            className="text-lg font-semibold text-primary"
                            href="#"
                        >
                            General
                        </Link>
                        <Link
                            className="text-lg font-semibold"
                            href="#"
                            onClick={toast}
                        >
                            Advanced
                        </Link>
                    </nav>
                    <General />
                </div>
            </div>
        </div>
    )
}
