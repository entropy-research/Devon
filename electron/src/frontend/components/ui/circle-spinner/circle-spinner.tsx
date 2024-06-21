import React from 'react'
import { cn } from '@/lib/utils'
import './circle-spinner.css' // Import the CSS file for the keyframes

interface CircleSpinnerProps {
    size?: 'sm' | 'lg',
    className?: string
}

const CircleSpinner: React.FC<CircleSpinnerProps> = ({
    size = 'sm',
    className,
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
                style={{ width: sizePx, height: sizePx }}
            ></div>
        </div>
    )
}

export default CircleSpinner
