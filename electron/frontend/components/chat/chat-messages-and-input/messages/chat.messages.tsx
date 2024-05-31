import {
    UserMessage,
    BotMessage,
    ToolResponseMessage,
    ThoughtMessage,
    SpinnerMessage,
} from '@/components/chat/chat-messages-and-input/messages/chat.message-variants'

export interface ChatMessages {
    messages: any[]
    spinning: boolean
}

const ChatMessages = ({ messages, spinning }: ChatMessages) => {
    return messages?.length ? (
        <div className="relative px-8 mt-5">
            {messages.map((message, index) => (
                <DisplayedChatMessage
                    key={message.id ?? index}
                    message={message}
                />
            ))}
            {spinning && <SpinnerMessage />}
        </div>
    ) : (
        <></>
    )
}

/**
ModelResponse
- Content: Response by the model (currently in the format <THOUGHT></THOUGHT><ACTION></ACTION>)
- Next: The action is parsed and the right tool is chosen or user response is requested

ToolResponse
- Content: Response from the tool
- Next: The model is called with the reponse as the observation

UserRequest
- Content: User input
- Next: The output is sent as ToolRequest

Interrupt
- Content: The interrupt message
- Next: ModelResponse, the model is interrupted

Stop
- Content: None
- Next: None

Task
- Content: The next task/object the agent has to complete
- Next: ModelResponse

 */
const DisplayedChatMessage = ({ message }) => {
    return (
        message.type && (
            <div className="mb-8">
                {message.type === 'agent' ? (
                    <BotMessage content={message.text}></BotMessage>
                ) : message.type === 'thought' ? (
                    <ThoughtMessage content={message.text}></ThoughtMessage>
                ) : message.type === 'command' ? (
                    <ChatTypeWrapper type="Command">
                        {message.text}
                    </ChatTypeWrapper>
                ) : message.type === 'tool' ? (
                    <ToolResponseMessage
                        content={message.text}
                    ></ToolResponseMessage>
                ) : message.type === 'user' ? (
                    <UserMessage>{message.text}</UserMessage>
                ) : message.type === 'task' ? (
                    <div className="border border-2 border-gray p-2 px-4 rounded-md">
                        <ChatTypeWrapper
                            type="Task"
                            className="text-gray-400 italic"
                        >
                            {message.text}
                        </ChatTypeWrapper>
                    </div>
                ) : (
                    // <ChatTypeWrapper type="(Type not found)">
                    //     {message.content}
                    // </ChatTypeWrapper>
                    <></>
                )}
            </div>
        )
    )
}

const ChatTypeWrapper = ({
    type,
    children,
    className,
}: {
    type: string
    children: any
    className?: string
}) => {
    return (
        <p className={className}>
            <span className="font-bold mr-2">{type}:</span>
            {children}
        </p>
    )
}

export default ChatMessages
