import { useState, useRef } from 'react'
import { Paperclip, ArrowRight } from 'lucide-react'
import { AutoresizeTextarea } from '@/components/ui/textarea'
import { useEnterSubmit } from '@/lib/hooks/chat.use-enter-submit'
import useCreateResponse from '@/lib/services/sessionService/use-create-response'
import useInterruptSession from '@/lib/services/sessionService/use-interrupt-session'
import { useSearchParams } from 'next/navigation'
import SelectProjectDirectoryModal from '@/components/modals/select-project-directory-modal'
import AtomLoader from '@/components/ui/atom-loader/atom-loader'

const Input = ({
    isAtBottom,
    scrollToBottom,
    setUserRequested,
    userRequested,
    modelLoading,
    viewOnly,
    isRunning,
    eventContext,
}: {
    isAtBottom: boolean
    scrollToBottom: () => void
    setUserRequested: (value: boolean) => void
    userRequested: boolean
    modelLoading: boolean
    viewOnly: boolean
    isRunning: boolean
    eventContext: any
}) => {
    const [focused, setFocused] = useState(false)
    const { formRef, onKeyDown } = useEnterSubmit()
    const inputRef = useRef<HTMLTextAreaElement>(null)
    const [input, setInput] = useState('')
    const { createResponse, responseData, loading, error } = useCreateResponse()
    const { interruptSession } = useInterruptSession()
    // For blocking user with modal
    const searchParams = useSearchParams()
    const [openProjectModal, setOpenProjectModal] = useState(false)

    async function submitUserMessage(value: string) {
        const chatId = searchParams.get('chat')
        // Distinguish between user request vs interrupt
        if (eventContext.userRequest) {
            setUserRequested(false)
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
            {(modelLoading || userRequested) && (
                <InformationBox
                    modelLoading={modelLoading}
                    userRequested={userRequested}
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

const InformationBox = ({ modelLoading, userRequested }) => {
    const types = {
        modelLoading: {
            text: 'Devon is working...',
        },
        userRequested: {
            text: 'Devon is waiting for your response',
        },
    }

    const currentType = modelLoading ? types.modelLoading : types.userRequested

    return (
        <div className="bg-fade-bottom-to-top2 py-5 px-3">
            <div className="flex items-center gap-4">
                <div className="relative flex justify-center items-center">
                    <div
                        className={`absolute w-4 h-4 rounded-full bg-primary animate-pulse blur-sm`}
                    ></div>
                    <AtomLoader />
                </div>
                <p className="italic text-gray-400">{currentType.text}</p>
            </div>
        </div>
    )
}

export default Input
