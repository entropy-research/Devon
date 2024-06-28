import { cn } from '@/lib/utils'
interface SpinnerProps {
    paused: boolean
}

export default function Spinner({ paused }: SpinnerProps) {
    return (
        <svg
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            viewBox="0 0 24 24"
            strokeLinecap="round"
            strokeLinejoin="round"
            xmlns="http://www.w3.org/2000/svg"
            className={cn('size-5 stroke-zinc-400', {
                "animate-[spin_1.7s_linear_infinite]": !paused,
            })}
        >
            <path d="M12 3v3m6.366-.366-2.12 2.12M21 12h-3m.366 6.366-2.12-2.12M12 21v-3m-6.366.366 2.12-2.12M3 12h3m-.366-6.366 2.12 2.12"></path>
        </svg>
    )
}
