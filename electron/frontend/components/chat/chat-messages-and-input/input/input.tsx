import { useState, useRef } from 'react'
import { Paperclip, ArrowRight, CirclePause } from 'lucide-react'
import { AutoresizeTextarea } from '@/components/ui/textarea'
import { useEnterSubmit } from '@/lib/hooks/chat.use-enter-submit'
import {
    useCreateResponse,
    useInterruptSession,
} from '@/lib/services/sessionService/sendUserMessage'
import { useSearchParams } from 'next/navigation'
import SelectProjectDirectoryModal from '@/components/modals/select-project-directory-modal'
import AtomLoader from '@/components/ui/atom-loader/atom-loader'

const Input = ({
    isAtBottom,
    scrollToBottom,
    viewOnly,
    eventContext,
    loading,
}: {
    isAtBottom: boolean
    scrollToBottom: () => void
    viewOnly: boolean
    eventContext: any
    loading: boolean
}) => {
    const [focused, setFocused] = useState(false)
    const { formRef, onKeyDown } = useEnterSubmit()
    const inputRef = useRef<HTMLTextAreaElement>(null)
    const [input, setInput] = useState('')
    const { createResponse } = useCreateResponse()
    const { interruptSession } = useInterruptSession()
    // For blocking user with modal
    const searchParams = useSearchParams()
    const [openProjectModal, setOpenProjectModal] = useState(false)

    async function submitUserMessage(value: string) {
        const chatId = searchParams.get('chat')
        // Distinguish between user request vs interrupt
        if (eventContext.userRequest) {
            // setUserRequested(false)
            return createResponse(chatId, value)
        }
        return interruptSession(chatId, value)
    }

    function checkShouldOpenModal() {
        const chatId = searchParams.get('chat')
        // If it's a new chat, open the project modal
        if (chatId && chatId === 'New') {
            setOpenProjectModal(true)
        }
    }

    function handleFocus() {
        setFocused(true)
        checkShouldOpenModal()
    }

    return (
        <div
            className={`w-full relative grid align-middle px-5 ${!viewOnly ? 'pb-7 mt-8' : ''}`}
        >
            {(loading ||
                eventContext.modelLoading ||
                eventContext.userRequest) && (
                <InformationBox
                    modelLoading={eventContext.modelLoading}
                    userRequested={eventContext.userRequest}
                    loading={loading}
                />
            )}
            {!viewOnly && (
                <>
                    <form
                        ref={formRef}
                        onSubmit={async (e: any) => {
                            e.preventDefault()

                            checkShouldOpenModal()

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
                                    className={`h-4 w-4 ${focused ? 'text-primary' : ''}`}
                                />
                            </button>
                        </div>
                    </form>
                    <SelectProjectDirectoryModal
                        openProjectModal={openProjectModal}
                        setOpenProjectModal={setOpenProjectModal}
                    />
                </>
            )}
        </div>
    )
}

const InformationBox = ({ modelLoading, userRequested, loading }) => {
    let paused = false
    const types: {
        [key: string]: {
            text: string
            accessory: JSX.Element
        }
    } = {
        modelLoading: {
            text: 'Devon is working...',
            accessory: <PauseButton paused={paused} />,
        },
        userRequested: {
            text: 'Devon is waiting for your response',
            accessory: <></>,
        },
        loading: {
            text: 'Devon is gathering himself...',
            accessory: <></>,
        },
    }

    let currentType
    if (loading) {
        currentType = types.loading
    } else {
        currentType = modelLoading ? types.modelLoading : types.userRequested
    }
    currentType = types.modelLoading
    if (paused) {
        currentType.text = 'Devon is paused'
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

export default Input

const PauseButton = ({ paused }) => {
    if (paused) {
        return (
            <button
                // onClick=
                className="flex items-center gap-2 px-3 py-1 rounded-md mb-[-4px] -mr-2 text-gray-100 smooth-hover"
            >
                <CirclePause size={16} />
                Paused
            </button>
        )
    }
    return (
        <button
            // onClick=
            className="flex items-center gap-2 px-3 py-1 rounded-md text-gray-400 mb-[-4px] -mr-2 hover:text-gray-100 smooth-hover"
        >
            <CirclePause size={16} />
            Pause
        </button>
    )
}
