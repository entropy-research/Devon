import React from 'react'
import './dots-spinner.css'

interface LoaderProps {
    color?: string
    size?: number
    duration?: number
    paused?: boolean
}

const DotsSpinner: React.FC<LoaderProps> = ({
    color,
    size,
    duration,
    paused,
}) => {
    const style: React.CSSProperties = {}

    if (color) style.color = color
    if (size) style['--d' as any] = `${size}px`
    if (duration) style.animationDuration = `${duration}s`

    return (
        <div
            className={`dots-spinner paused`}
            style={style}
        />
    )
}

export default DotsSpinner
