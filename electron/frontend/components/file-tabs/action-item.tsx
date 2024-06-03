import { Dialog, DialogTrigger } from '@/components/ui/dialog'

// For FileTabs component: The button on the right side of the tabs area. Opens a dialog with passed-in content
const ActionItem = ({
    active,
    icon,
    dialogContent,
    clickAction,
}: {
    active: boolean
    icon: JSX.Element
    dialogContent?: JSX.Element
    clickAction?: () => void
}) =>
    dialogContent ? (
        <DialogWrapper
            triggerButton={
                <StyledButton isTrigger active={active} icon={icon} />
            }
        >
            {dialogContent}
        </DialogWrapper>
    ) : (
        <StyledButton active={active} icon={icon} clickAction={clickAction} />
    )

const DialogWrapper = ({ triggerButton, children }) => (
    <Dialog>
        {triggerButton}
        {children}
    </Dialog>
)

const StyledButton = ({
    active,
    icon,
    clickAction,
    isTrigger,
}: {
    active: boolean
    icon: JSX.Element
    clickAction?: () => void
    isTrigger?: boolean
}) =>
    isTrigger ? (
        <DialogTrigger asChild>
            <button
                className={`w-8 h-8 flex items-center justify-center rounded-md transition duration-200 hover:bg-gray-100 dark:hover:bg-batman ${active ? 'bg-gray-100 dark:bg-batman' : ''}`}
            >
                {icon}
            </button>
        </DialogTrigger>
    ) : (
        <button
            onClick={clickAction}
            className={`w-8 h-8 flex items-center justify-center rounded-md transition duration-200 hover:bg-gray-100 dark:hover:bg-batman ${active ? 'bg-gray-100 dark:bg-batman' : ''}`}
        >
            {icon}
        </button>
    )

export default ActionItem
