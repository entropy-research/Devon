import { useEffect, useState, useRef, RefObject } from 'react'
import {
    Gitgraph,
    TemplateName,
    templateExtend,
} from '@/components/ui/timeline-pkg/timeline'
import './timeline.css'

export function TimelineWidget({ className }: { className?: string }) {
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
type SubStepType = {
    id: number
    label: string
    subtitle: string
}

type StepType = {
    id: number
    label: string
    subtitle: string
    subSteps: SubStepType[]
}

const steps: StepType[] = [
    {
        id: 1,
        label: 'Initialize the project',
        subtitle: 'Setting up the initial project structure',
        subSteps: [
            {
                id: 1.1,
                label: 'Install dependencies',
                subtitle: 'Add necessary packages',
            },
            {
                id: 1.2,
                label: 'Create project files',
                subtitle: 'Setup basic file structure',
            },
        ],
    },
    {
        id: 2,
        label: 'Create the game loop',
        subtitle: 'Implement the main game loop',
        subSteps: [
            {
                id: 2.1,
                label: 'Define game loop logic',
                subtitle: 'Setup the game loop function',
            },
        ],
    },
    {
        id: 3,
        label: 'Add snake logic',
        subtitle: 'Implement the snake movement and controls',
        subSteps: [],
    },
    {
        id: 4,
        label: 'Implement the game board',
        subtitle: 'Design and code the game board layout',
        subSteps: [],
    },
    {
        id: 5,
        label: 'Add collision detection',
        subtitle: 'Implement logic to detect collisions',
        subSteps: [],
    },
    {
        id: 6,
        label: 'Add food and scoring',
        subtitle: 'Add food items and scoring mechanism',
        subSteps: [],
    },
    {
        id: 7,
        label: 'Finalize the game',
        subtitle: 'Finish up and test the game',
        subSteps: [],
    },
]

const VerticalStepper: React.FC = () => {
    const [activeStep, setActiveStep] = useState(0)
    const [subStepFinished, setSubStepFinished] = useState(false)

    useEffect(() => {
        if (activeStep < steps.length) {
            const timer = setTimeout(() => {
                if (
                    subStepFinished ||
                    steps[activeStep].subSteps.length === 0
                ) {
                    setActiveStep(activeStep + 1)
                    setSubStepFinished(false)
                }
            }, 2000)
            return () => clearTimeout(timer)
        }
    }, [activeStep, subStepFinished])

    return (
        <div className="flex flex-col h-full w-full px-5 mt-10">
            <div className="relative">
                <div className="absolute inset-0 flex flex-col w-full">
                    {steps.map((step, index) => (
                        <Step
                            key={step.id}
                            step={step}
                            index={index}
                            activeStep={activeStep}
                            setSubStepFinished={setSubStepFinished}
                        />
                    ))}
                </div>
            </div>
        </div>
    )
}

const Step: React.FC<{
    step: StepType
    index: number
    activeStep: number
    setSubStepFinished: (value: boolean) => void
}> = ({ step, index, activeStep, setSubStepFinished }) => {
    const [subStepActiveIndex, setSubStepActiveIndex] = useState(-1)
    const [connectorHeight, setConnectorHeight] = useState(0)
    const contentRef: RefObject<HTMLDivElement> = useRef(null)
    const pathRef: RefObject<SVGPathElement> = useRef(null)
    const CURVE_SVG_WIDTH = 65
    const CURVE_SVG_HEIGHT_OFFSET = 50

    useEffect(() => {
        if (contentRef.current) {
            const totalHeight = contentRef.current.clientHeight + CURVE_SVG_HEIGHT_OFFSET
            setConnectorHeight(totalHeight)
        }
    }, [contentRef.current])

    useEffect(() => {
        if (activeStep === index && step.subSteps.length > 0) {
            const interval = setInterval(() => {
                setSubStepActiveIndex(prevIndex => {
                    if (prevIndex < step.subSteps.length - 1) {
                        return prevIndex + 1
                    }
                    clearInterval(interval)
                    setSubStepFinished(true)
                    return prevIndex
                })
            }, 1000)
            return () => clearInterval(interval)
        } else if (activeStep === index) {
            setSubStepFinished(true)
        }
    }, [activeStep, index, setSubStepFinished, step.subSteps.length])

    useEffect(() => {
        if (pathRef.current) {
            const pathLength = pathRef.current.getTotalLength()
            pathRef.current.style.strokeDasharray = `${CURVE_SVG_WIDTH}`
            pathRef.current.style.strokeDashoffset = `${CURVE_SVG_WIDTH}`
            pathRef.current.getBoundingClientRect()
            pathRef.current.style.transition =
                'stroke-dashoffset 2s ease-in-out'
            pathRef.current.style.strokeDashoffset = '0'
        }
    }, [connectorHeight])

    const connectorPath = `
        M 12 0
        Q 12 ${connectorHeight / 2} ${CURVE_SVG_WIDTH} ${connectorHeight / 2}
    `

    return (
        <div className="flex flex-row">
            <div className="relative flex-start">
                <div
                    className={`z-10 flex items-center justify-center w-6 h-6 bg-white rounded-full ${activeStep >= index ? 'opacity-100' : 'opacity-0'} transition-opacity duration-1000`}
                >
                    {index === 0 && (
                        <div className="w-3 h-3 bg-primary rounded-full"></div>
                    )}
                    {index !== 0 && (
                        <div className="w-2 h-2 bg-white rounded-full"></div>
                    )}
                </div>
                {index < steps.length - 1 && (
                    <div
                        className={`absolute w-px ${activeStep > index ? 'h-full' : 'h-0'} bg-white top-6 left-1/2 transform -translate-x-1/2 transition-all duration-1000`}
                    ></div>
                )}
                {step.subSteps.length > 0 && subStepActiveIndex >= 0 && (
                    <svg
                        width={CURVE_SVG_WIDTH}
                        height={connectorHeight}
                        className="absolute"
                    >
                        <path
                            ref={pathRef}
                            d={connectorPath}
                            stroke="white"
                            fill="transparent"
                            strokeWidth="2"
                        />
                    </svg>
                )}
            </div>
            <div
                className={`flex items-center ml-5 mb-3 ${activeStep >= index ? 'opacity-100' : 'opacity-0'} transition-opacity duration-1000 delay-800`}
            >
                <div className="flex flex-col">
                    <div ref={contentRef} className="flex flex-col">
                        <span className="text-white">{step.label}</span>
                        <span className="mt-1 text-gray-400">
                            {step.subtitle}
                        </span>
                    </div>
                    {activeStep >= index && step.subSteps.length > 0 && (
                        <div className="ml-5 mt-3">
                            {step.subSteps.map((subStep, subIndex) => (
                                <SubStep
                                    key={subStep.id}
                                    subStep={subStep}
                                    showLine={
                                        subIndex < step.subSteps.length - 1
                                    }
                                    active={subStepActiveIndex >= subIndex}
                                />
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

const SubStep: React.FC<{
    subStep: SubStepType
    showLine: boolean
    active: boolean
}> = ({ subStep, showLine, active }) => {
    return (
        <div className="relative flex flex-col pb-3">
            <div className="flex">
                <div
                    className={`z-10 flex items-center justify-center w-4 h-4 bg-gray-400 rounded-full translate-y-1 ${active ? 'opacity-100' : 'opacity-0'} transition-opacity duration-1000`}
                >
                    <div className="w-2 h-2 bg-white rounded-full"></div>
                </div>
                <div
                    className={`ml-3 ${active ? 'opacity-100' : 'opacity-0'} transition-opacity duration-1000 delay-800`}
                >
                    <span className="text-white">{subStep.label}</span>
                    <span className="block mt-1 text-gray-400">
                        {subStep.subtitle}
                    </span>
                </div>
            </div>
            {showLine && (
                <div
                    className={`absolute w-px ${active ? 'h-full' : 'h-0'} bg-gray-400 left-2 transform translate-y-3 -translate-x-1/2 transition-all duration-1000`}
                ></div>
            )}
        </div>
    )
}

export default VerticalStepper
