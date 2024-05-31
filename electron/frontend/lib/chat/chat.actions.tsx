'use server'
// import 'server-only'

import {
    createAI,
    createStreamableUI,
    getMutableAIState,
    getAIState,
    render,
    createStreamableValue,
} from 'ai/rsc'
import OpenAI from 'openai'

import {
    BotCard,
    BotMessage,
    //   Stock,
    //   Purchase
} from '@/components/chat/chat-messages-and-input/messages/chat.message-types'

// import {
//   spinner,
//   BotCard,
//   BotMessage,
//   SystemMessage,
//   Stock,
//   Purchase
// } from '@/components/stocks'

import { z } from 'zod'
// import { EventsSkeleton } from '@/components/stocks/events-skeleton'
// import { Events } from '@/components/stocks/events'
// import { StocksSkeleton } from '@/components/stocks/stocks-skeleton'
// import { Stocks } from '@/components/stocks/stocks'
// import { StockSkeleton } from '@/components/stocks/stock-skeleton'
import {
    //   formatNumber,
    //   runAsyncFnWithoutBlocking,
    sleep,
    nanoid,
} from '@/lib/chat.utils'
import { saveChat } from '@/app/chat.actions'
import {
    SpinnerMessage,
    UserMessage,
} from '@/components/chat/chat-messages-and-input/messages/chat.message-types'
import { Chat } from '@/lib/chat.types'
import { auth } from '@/chat.auth'

const StockSkeleton = () => <div>StockSkeleton</div>

const StocksSkeleton = () => <div>StocksSkeleton</div>

const EventsSkeleton = () => <div>EventsSkeleton</div>

const Stock = props => <div>Stock</div>

const Stocks = props => <div>Stock</div>

const Purchase = props => <div>Purchase</div>

const Events = props => <div>Events</div>

const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY || '',
})

// async function confirmPurchase(symbol: string, price: number, amount: number) {
//   'use server'

//   const aiState = getMutableAIState<typeof AI>()

//   const purchasing = createStreamableUI(
//     <div className="inline-flex items-start gap-1 md:items-center">
//       {spinner}
//       <p className="mb-2">
//         Purchasing {amount} ${symbol}...
//       </p>
//     </div>
//   )

//   const systemMessage = createStreamableUI(null)

//   runAsyncFnWithoutBlocking(async () => {
//     await sleep(1000)

//     purchasing.update(
//       <div className="inline-flex items-start gap-1 md:items-center">
//         {spinner}
//         <p className="mb-2">
//           Purchasing {amount} ${symbol}... working on it...
//         </p>
//       </div>
//     )

//     await sleep(1000)

//     purchasing.done(
//       <div>
//         <p className="mb-2">
//           You have successfully purchased {amount} ${symbol}. Total cost:{' '}
//           {formatNumber(amount * price)}
//         </p>
//       </div>
//     )

//     systemMessage.done(
//       <SystemMessage>
//         You have purchased {amount} shares of {symbol} at ${price}. Total cost ={' '}
//         {formatNumber(amount * price)}.
//       </SystemMessage>
//     )

//     aiState.done({
//       ...aiState.get(),
//       messages: [
//         ...aiState.get().messages.slice(0, -1),
//         {
//           id: nanoid(),
//           role: 'function',
//           name: 'showStockPurchase',
//           content: JSON.stringify({
//             symbol,
//             price,
//             defaultAmount: amount,
//             status: 'completed'
//           })
//         },
//         {
//           id: nanoid(),
//           role: 'system',
//           content: `[User has purchased ${amount} shares of ${symbol} at ${price}. Total cost = ${
//             amount * price
//           }]`
//         }
//       ]
//     })
//   })

//   return {
//     purchasingUI: purchasing.value,
//     newMessage: {
//       id: nanoid(),
//       display: systemMessage.value
//     }
//   }
// }

async function submitUserMessage(content: string) {
    'use server'

    const aiState = getMutableAIState<typeof AI>()

    aiState.update({
        ...aiState.get(),
        messages: [
            ...aiState.get().messages,
            {
                id: nanoid(),
                role: 'user',
                content,
            },
        ],
    })

    let textStream: undefined | ReturnType<typeof createStreamableValue<string>>
    let textNode: undefined | React.ReactNode

    const ui = render({
        model: 'gpt-3.5-turbo',
        provider: openai,
        initial: <SpinnerMessage />,
        messages: [
            {
                role: 'system',
                content: `\
                You are Devon, an AI software engineer designed to help users solve coding tasks and fix or solve GitHub issues in their codebase. You can guide users through debugging processes, offer solutions to programming problems, and write the code to solve it.

                Messages inside [] signify a UI element or a user event. For example:
                
                "[Current Issue = Memory Leak]" indicates that there is an interface showing an issue related to a memory leak.
                "[User has tagged issue #123 as critical]" means that the user has changed the priority of issue #123 to critical in the UI.
                If the user requests help with a specific coding problem, use show_solution_ui to display potential fixes or code suggestions.
                If the user wants to understand a particular error or issue, use show_error_details to provide insights and detailed explanations.
                If you want to list open issues or tasks, use list_github_issues.
                If the user wants to update or close a GitHub issue, use update_github_issue_ui.
                
                In addition to these tasks, you can chat with users about software development best practices and perform code reviews if needed. If the user asks for something outside of your programming capabilities, respond that you are a demo and can only provide guidance within the scope of software engineering and GitHub management.`,
            },
            ...aiState.get().messages.map((message: any) => ({
                role: message.role,
                content: message.content,
                name: message.name,
            })),
        ],
        text: ({ content, done, delta }) => {
            if (!textStream) {
                textStream = createStreamableValue('')
                textNode = <BotMessage content={textStream.value} />
            }

            if (done) {
                textStream.done()
                aiState.done({
                    ...aiState.get(),
                    messages: [
                        ...aiState.get().messages,
                        {
                            id: nanoid(),
                            role: 'assistant',
                            content,
                        },
                    ],
                })
            } else {
                textStream.update(delta)
            }

            return textNode
        },
        functions: {
            listStocks: {
                description: 'List three imaginary stocks that are trending.',
                parameters: z.object({
                    stocks: z.array(
                        z.object({
                            symbol: z
                                .string()
                                .describe('The symbol of the stock'),
                            price: z
                                .number()
                                .describe('The price of the stock'),
                            delta: z
                                .number()
                                .describe('The change in price of the stock'),
                        })
                    ),
                }),
                render: async function* ({ stocks }) {
                    yield (
                        <BotCard>
                            <StocksSkeleton />
                        </BotCard>
                    )

                    await sleep(1000)

                    aiState.done({
                        ...aiState.get(),
                        messages: [
                            ...aiState.get().messages,
                            {
                                id: nanoid(),
                                role: 'function',
                                name: 'listStocks',
                                content: JSON.stringify(stocks),
                            },
                        ],
                    })

                    return (
                        <BotCard>
                            <Stocks props={stocks} />
                        </BotCard>
                    )
                },
            },
            showStockPrice: {
                description:
                    'Get the current stock price of a given stock or currency. Use this to show the price to the user.',
                parameters: z.object({
                    symbol: z
                        .string()
                        .describe(
                            'The name or symbol of the stock or currency. e.g. DOGE/AAPL/USD.'
                        ),
                    price: z.number().describe('The price of the stock.'),
                    delta: z
                        .number()
                        .describe('The change in price of the stock'),
                }),
                render: async function* ({ symbol, price, delta }) {
                    yield (
                        <BotCard>
                            <StockSkeleton />
                        </BotCard>
                    )

                    await sleep(1000)

                    aiState.done({
                        ...aiState.get(),
                        messages: [
                            ...aiState.get().messages,
                            {
                                id: nanoid(),
                                role: 'function',
                                name: 'showStockPrice',
                                content: JSON.stringify({
                                    symbol,
                                    price,
                                    delta,
                                }),
                            },
                        ],
                    })

                    return (
                        <BotCard>
                            <Stock props={{ symbol, price, delta }} />
                        </BotCard>
                    )
                },
            },
            showStockPurchase: {
                description:
                    'Show price and the UI to purchase a stock or currency. Use this if the user wants to purchase a stock or currency.',
                parameters: z.object({
                    symbol: z
                        .string()
                        .describe(
                            'The name or symbol of the stock or currency. e.g. DOGE/AAPL/USD.'
                        ),
                    price: z.number().describe('The price of the stock.'),
                    numberOfShares: z
                        .number()
                        .describe(
                            'The **number of shares** for a stock or currency to purchase. Can be optional if the user did not specify it.'
                        ),
                }),
                render: async function* ({
                    symbol,
                    price,
                    numberOfShares = 100,
                }) {
                    if (numberOfShares <= 0 || numberOfShares > 1000) {
                        aiState.done({
                            ...aiState.get(),
                            messages: [
                                ...aiState.get().messages,
                                {
                                    id: nanoid(),
                                    role: 'system',
                                    content: `[User has selected an invalid amount]`,
                                },
                            ],
                        })

                        return <BotMessage content={'Invalid amount'} />
                    }

                    aiState.done({
                        ...aiState.get(),
                        messages: [
                            ...aiState.get().messages,
                            {
                                id: nanoid(),
                                role: 'function',
                                name: 'showStockPurchase',
                                content: JSON.stringify({
                                    symbol,
                                    price,
                                    numberOfShares,
                                }),
                            },
                        ],
                    })

                    return (
                        <BotCard>
                            <Purchase
                                props={{
                                    numberOfShares,
                                    symbol,
                                    price: +price,
                                    status: 'requires_action',
                                }}
                            />
                        </BotCard>
                    )
                },
            },
            getEvents: {
                description:
                    'List funny imaginary events between user highlighted dates that describe stock activity.',
                parameters: z.object({
                    events: z.array(
                        z.object({
                            date: z
                                .string()
                                .describe(
                                    'The date of the event, in ISO-8601 format'
                                ),
                            headline: z
                                .string()
                                .describe('The headline of the event'),
                            description: z
                                .string()
                                .describe('The description of the event'),
                        })
                    ),
                }),
                render: async function* ({ events }) {
                    yield (
                        <BotCard>
                            <EventsSkeleton />
                        </BotCard>
                    )

                    await sleep(1000)

                    aiState.done({
                        ...aiState.get(),
                        messages: [
                            ...aiState.get().messages,
                            {
                                id: nanoid(),
                                role: 'function',
                                name: 'getEvents',
                                content: JSON.stringify(events),
                            },
                        ],
                    })

                    return (
                        <BotCard>
                            <Events props={events} />
                        </BotCard>
                    )
                },
            },
        },
    })

    return {
        id: nanoid(),
        display: ui,
    }
}

export type Message = {
    role: 'user' | 'assistant' | 'system' | 'function' | 'data' | 'tool'
    content: string
    id: string
    name?: string
}

export type AIState = {
    chatId: string
    messages: Message[]
}

export type UIState = {
    id: string
    display: React.ReactNode
}[]

export const AI = createAI<AIState, UIState>({
    actions: {
        submitUserMessage,
        // confirmPurchase
    },
    initialUIState: [],
    initialAIState: {
        chatId: nanoid(),
        messages: [
            {
                id: nanoid(),
                role: 'user',
                content: `\
        You are Devon, an AI software engineer designed to help users solve coding tasks and fix or solve GitHub issues in their codebase. You can guide users through debugging processes, offer solutions to programming problems, and write the code to solve it.`,
            },
        ],
    },
    onGetUIState: async () => {
        'use server'

        const session = await auth()

        if (session && session.user) {
            const aiState = getAIState()

            if (aiState) {
                const uiState = getUIStateFromAIState(aiState)
                return uiState
            }
        } else {
            return
        }
    },
    onSetAIState: async ({ state, done }) => {
        'use server'

        const session = await auth()

        if (session && session.user) {
            const { chatId, messages } = state

            const createdAt = new Date()
            const userId = session.user.id as string
            const path = `/?chat=${chatId}`
            const title = messages[0].content.substring(0, 100)

            const chat: Chat = {
                id: chatId,
                title,
                userId,
                createdAt,
                messages,
                path,
            }

            await saveChat(chat)
        } else {
            return
        }
    },
})

export const getUIStateFromAIState = (aiState: Chat) => {
    return aiState.messages
        ?.filter(message => message.role !== 'system')
        .map((message, index) => ({
            id: `${aiState.chatId}-${index}`,
            display:
                // message.role === 'function' ? (
                //   message.name === 'listStocks' ? (
                //     <BotCard>
                //       <Stocks props={JSON.parse(message.content)} />
                //     </BotCard>
                //   ) : message.name === 'showStockPrice' ? (
                //     <BotCard>
                //       <Stock props={JSON.parse(message.content)} />
                //     </BotCard>
                //   ) : message.name === 'showStockPurchase' ? (
                //     <BotCard>
                //       <Purchase props={JSON.parse(message.content)} />
                //     </BotCard>
                //   ) : message.name === 'getEvents' ? (
                //     <BotCard>
                //       <Events props={JSON.parse(message.content)} />
                //     </BotCard>
                //   ) : null
                // ) : message.role === 'user' ? (
                //   <UserMessage>{message.content}</UserMessage>
                // ) : (
                //   <BotMessage content={message.content} />
                // )
                message.role === 'user' ? (
                    <UserMessage>{message.content}</UserMessage>
                ) : (
                    <BotMessage content={message.content} />
                ),
        }))
}
