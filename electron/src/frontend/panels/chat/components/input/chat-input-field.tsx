import { useState, useRef, useEffect } from 'react'
import {
    Paperclip,
    ArrowRight,
    CirclePause,
    Axis3DIcon,
    CirclePlay,
} from 'lucide-react'
import { AutoresizeTextarea } from '@/components/ui/textarea'
import { useEnterSubmit } from '@/panels/chat/lib/hooks/chat.use-enter-submit'
import SelectProjectDirectoryModal from '@/components/modals/select-project-directory-modal'
import AtomLoader from '@/components/ui/atom-loader/atom-loader'
import { SessionMachineContext } from '@/contexts/session-machine-context'
import { useBackendUrl } from '@/contexts/backend-url-context'
import { useAtom } from 'jotai'
import { selectedCodeSnippetAtom } from '@/panels/editor/components/code-editor'

const ChatInputField = ({
    isAtBottom,
    scrollToBottom,
    viewOnly,
    eventContext,
    loading,
    sessionId,
}: {
    isAtBottom: boolean
    scrollToBottom: () => void
    viewOnly: boolean
    eventContext: any
    loading: boolean
    sessionId: string
}) => {
    const [focused, setFocused] = useState(false)
    // const [paused, setPaused] = useState(false)
    const { formRef, onKeyDown } = useEnterSubmit()
    const inputRef = useRef<HTMLTextAreaElement>(null)
    const [input, setInput] = useState('')
    const [selectedCodeSnippet, setSelectedCodeSnippet] = useAtom<
        string | null
    >(selectedCodeSnippetAtom)

    // For blocking user with modal
    // const searchParams = useSearchParams()
    const [openProjectModal, setOpenProjectModal] = useState(false)
    const { backendUrl } = useBackendUrl()

    const sessionActorRef = SessionMachineContext.useActorRef()

    useEffect(() => {
        if (selectedCodeSnippet) {
            setInput(prevInput => prevInput + '\n' + selectedCodeSnippet)
            setSelectedCodeSnippet(null)
        }
    }, [selectedCodeSnippet, setSelectedCodeSnippet])

    async function submitUserMessage(value: string) {
        sessionActorRef.send({ type: 'session.sendMessage', message: value })
    }

    // function checkShouldOpenModal() {
    //     const chatId = searchParams.get('chat')
    //     // If it's a new chat, open the project modal
    //     if (chatId && chatId === 'New') {
    //         setOpenProjectModal(true)
    //     }
    // }

    function handleFocus() {
        setFocused(true)
        // checkShouldOpenModal()
    }

    async function handlePause() {
        sessionActorRef.send({ type: 'session.toggle' })
    }

    return (
        <div
            className={`w-full relative grid align-middle px-5 ${
                !viewOnly ? 'pb-7 mt-8' : ''
            }`}
        >
            {(loading ||
                eventContext.modelLoading ||
                eventContext.userRequest ||
                sessionActorRef.getSnapshot().matches('paused') ||
                sessionActorRef.getSnapshot().matches('running')) && (
                <InformationBox
                    modelLoading={eventContext.modelLoading}
                    userRequested={eventContext.userRequest}
                    loading={loading}
                    paused={sessionActorRef.getSnapshot().matches('paused')}
                    pauseHandler={handlePause}
                />
            )}
            {!viewOnly && (
                <>
                    <form
                        ref={formRef}
                        onSubmit={async (e: any) => {
                            e.preventDefault()

                            // checkShouldOpenModal()

                            // Blur focus on mobile
                            if (window.innerWidth < 600) {
                                e.target['message']?.blur()
                            }

                            const value = input.trim()
                            setInput('')
                            if (!value) return

                            const res = await submitUserMessage(value)

                            scrollToBottom()
                        }}
                    >
                        <div className="relative">
                            <AutoresizeTextarea
                                ref={inputRef}
                                placeholder="Send a message to Devon ..."
                                onFocus={handleFocus}
                                onBlur={() => setFocused(false)}
                                rows={1}
                                onKeyDown={onKeyDown}
                                value={input}
                                onChange={e => setInput(e.target.value)}
                                disabled={loading}
                            />
                            {selectedCodeSnippet && (
                                <div className="mt-2 p-2 bg-gray-100 rounded">
                                    <pre className="text-sm">
                                        {selectedCodeSnippet}
                                    </pre>
                                </div>
                            )}
                            {/* <button
                                onClick={toast}
                                className="absolute left-[0.5rem] top-1/2 -translate-y-1/2 xl:left-[0.75rem] flex h-8 w-8 items-center justify-center rounded-md smooth-hover"
                            >
                                <Paperclip
                                    className={`h-4 w-4 ${focused ? 'text-primary' : ''}`}
                                />
                            </button> */}
                            <button
                                className="absolute right-2 top-1/2 h-4 w-4 -translate-y-1/2 xl:right-4"
                                type="submit"
                            >
                                <ArrowRight
                                    className={`h-4 w-4 ${
                                        focused ? 'text-primary' : ''
                                    }`}
                                />
                            </button>
                        </div>
                    </form>
                    {/* <SelectProjectDirectoryModal
                        openProjectModal={openProjectModal}
                        setOpenProjectModal={setOpenProjectModal}
                        backendUrl={backendUrl}
                    /> */}
                </>
            )}
        </div>
    )
}

const InformationBox = ({
    modelLoading,
    userRequested,
    loading,
    paused,
    pauseHandler,
}: {
    modelLoading: boolean
    userRequested: boolean
    loading: boolean
    paused: boolean
    pauseHandler: () => void
}) => {
    const types: {
        [key: string]: {
            text: string
            accessory: JSX.Element
        }
    } = {
        modelLoading: {
            text: 'Devon is working...',
            accessory: (
                <PauseButton paused={paused} pauseHandler={pauseHandler} />
            ),
        },
        userRequested: {
            text: 'Devon is waiting for your response',
            accessory: <></>,
        },
        loading: {
            text: 'Devon is gathering himself...',
            accessory: <></>,
        },
        paused: {
            text: 'Devon is taking a coffee break (paused)',
            accessory: (
                <PauseButton paused={paused} pauseHandler={pauseHandler} />
            ),
        },
    }

    let currentType
    if (loading) {
        currentType = types.loading
    } else if (modelLoading) {
        currentType = types.modelLoading
    } else if (userRequested) {
        currentType = types.userRequested
    } else if (paused) {
        currentType = types.paused
    } else {
        currentType = types.loading
    }

    return (
        <div className="bg-fade-bottom-to-top2 py-5 px-1">
            <div className="flex items-end justify-between">
                <div className="flex items-center gap-3">
                    <AtomLoader />
                    <p className="italic text-gray-400">{currentType.text}</p>
                </div>
                {currentType.accessory}
            </div>
        </div>
    )
}

export default ChatInputField

const PauseButton = ({
    paused,
    pauseHandler,
}: {
    paused: boolean
    pauseHandler: () => void
}) => {
    if (paused) {
        return (
            <button
                onClick={pauseHandler}
                className="flex items-center gap-2 px-3 py-1 rounded-md mb-[-4px] -mr-2 text-gray-100 smooth-hover"
            >
                <CirclePlay size={16} />
                Play
            </button>
        )
    }
    return (
        <button
            onClick={pauseHandler}
            className="flex items-center gap-2 px-3 py-1 rounded-md text-gray-400 mb-[-4px] -mr-2 hover:text-gray-100 smooth-hover"
        >
            <CirclePause size={16} />
            Pause
        </button>
    )
}
