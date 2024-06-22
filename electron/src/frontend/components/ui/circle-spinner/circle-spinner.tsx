import React from 'react'
import { cn } from '@/lib/utils'
import './circle-spinner.css'

interface CircleSpinnerProps {
    size?: 'sm' | 'lg'
    className?: string
    color?: string
}

const CircleSpinner: React.FC<CircleSpinnerProps> = ({
    size = 'sm',
    className,
    color = '#eab308', // Default color
}) => {
    const sizePx = size === 'lg' ? 50 : 15

    return (
        <div
            className={cn(
                'relative flex justify-center items-center',
                className
            )}
        >
            <div
                className="circle-loader"
                style={
                    {
                        width: sizePx,
                        height: sizePx,
                        '--spinner-color': color,
                    } as React.CSSProperties
                }
            ></div>
        </div>
    )
}

export default CircleSpinner
