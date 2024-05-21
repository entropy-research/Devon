export default function Header({
    sessionId,
    headerIcon,
}: {
    sessionId?: string
    headerIcon?: JSX.Element
}) {
    // if (!sessionId || sessionId === 'New') {
    //     return <></>
    // }
    return (
        <div className="items-center pb-3 border-outline-night shrink-0 items-left mt-2 flex flex-row justify-between border-b pl-[2rem]">
            {/* <div className="">
                <p className="text-lg mb-2">Hey there!</p>
                <p className="text-gray-400 text-sm">{`My name is Devon and I'm a software engineer. Give me coding tasks and I will try my best to solve them!`}</p>
            </div> */}
            <p className="text-lg">Create a snake game</p>

            {headerIcon}
        </div>
    )
}
