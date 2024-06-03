import Link from 'next/link'

function SidebarItem({
    icon,
    text,
    active,
    route,
    alert,
    expanded
}: {
    icon: JSX.Element
    text: string
    active: boolean
    route: string
    alert: boolean,
    expanded: boolean
}) {

    return (
        <div
            className={`
        relative flex py-2 px-3 my-1
        font-medium rounded-md cursor-pointer
        transition-colors group
    `}
        >
            <Link href={route} className="flex items-center">
                {expanded && icon}
                <span
                    className={`overflow-hidden transition-all flex items-center ${
                        expanded ? 'w-52 ml-[9px] py-2' : 'w-0'
                    }`}
                >
                    {expanded && text}
                </span>
            </Link>
            {alert && (
                <div
                    className={`absolute right-2 w-2 h-2 rounded bg-primary ${
                        expanded ? '' : 'top-2'
                    }`}
                />
            )}
        </div>
    )
}

export default SidebarItem