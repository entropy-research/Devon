import { Gitgraph, TemplateName, templateExtend } from '@gitgraph/react'
import './timeline.css'

function timeline(gitgraph) {
    const main = gitgraph.branch({
        name: 'main',
        style: {
            label: {
                bgColor: 'black',
                color: 'white',
            },
        },
    })
    main.commit({
        subject: 'Initial commit',
        // body: 'More details about the feature…',
        // dotText: '❤️',
        // tag: 'v1.2',
    })

    const develop = main.branch({
        name: 'develop',
        style: {
            // color: 'black',
            label: {
                bgColor: 'black',
                color: 'white',
            },
        },
    })

    // Step 1: Initialize the project
    develop.commit('Initialize the project')

    // Step 2: Create the game loop
    develop.commit('Create the game loop')

    // Step 3: Add snake logic
    develop.commit('Add snake logic')

    // Step 4: Implement the game board
    develop.commit('Implement the game board')

    // Step 5: Add collision detection
    develop.commit('Add collision detection')

    // Step 6: Add food and scoring
    develop.commit('Add food and scoring')

    // Step 7: Finalize the game
    develop.commit('Finalize the game')

    main.merge(develop)
}

export default function TimelineWidget({ className }: { className?: string }) {
    return (
        // <div className="h-full mt-[120px] flex w-full">
        //     <div className="bg-batman w-full min-w-[300px] h-[500px] p-5 rounded-lg">
        //         <p className="text-lg font-semibold">Timeline</p>
        //     </div>
        // </div>
        <div className={`flex h-full pb-[14px] ${className}`}>
            <div className="flex bg-batman overflow-y-scroll border border-neutral-600 ml-3  rounded-md">
                {/* <p className="text-lg font-semibold mb-3">Timeline</p> */}
                <div className="timeline pt-8">
                    <Gitgraph
                        options={{
                            template: templateExtend(TemplateName.Metro, {
                                colors: ['#d4d4d4', '#d4d4d4', '#d4d4d4'],
                            }),
                            author: ' ',
                            // generateCommitHash: () => ' ',
                        }}
                    >
                        {gitgraph => {
                            const main = gitgraph.branch({
                                name: 'main',
                                style: {
                                    label: {
                                        bgColor: 'black',
                                        color: '#d4d4d4',
                                    },
                                },
                            })
                            main.commit({
                                subject: 'Initial commit',
                                // body: 'More details about the feature…',
                                // dotText: '❤️',
                                // tag: 'v1.2',
                            })

                            const develop = main.branch({
                                name: 'develop',
                                style: {
                                    // color: 'black',
                                    label: {
                                        bgColor: 'black',
                                        color: '#d4d4d4',
                                    },
                                },
                            })

                            // Step 1: Initialize the project
                            develop.commit('Initialize the project')

                            // Step 2: Create the game loop
                            develop.commit('Create the game loop')

                            // Step 3: Add snake logic
                            develop.commit('Add snake logic')

                            // Step 4: Implement the game board
                            develop.commit('Implement the game board')

                            // Step 5: Add collision detection
                            develop.commit('Add collision detection')

                            // Step 6: Add food and scoring
                            develop.commit('Add food and scoring')

                            // Step 7: Finalize the game
                            develop.commit('Finalize the game')

                            // main.merge(develop)
                        }}
                    </Gitgraph>
                </div>
            </div>
        </div>
    )
}
