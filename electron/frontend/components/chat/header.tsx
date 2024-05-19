export default function Header({ sessionId }: { sessionId?: string }) {
    // if (!sessionId || sessionId === 'New') {
    //     return <></>
    // }
    return <></>
    return (
        <div className="shrink-0 items-left mt-5 flex flex-col justify-between border-b border-outline-day pb-5 px-[2rem] dark:border-outline-night">
            <>
                <p className="text-lg mb-2">Hey there!</p>
                <p className="text-gray-400 text-sm">{`My name is Devon and I'm a software engineer. Give me coding tasks and I will try my best to solve them!`}</p>
            </>
        </div>
    )
}
