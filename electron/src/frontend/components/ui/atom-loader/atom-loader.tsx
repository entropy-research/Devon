import React from 'react'
import './atom.css' // Import the CSS file for the keyframes

interface AtomLoaderProps {
    size?: 'sm' | 'lg' | 'xs'
    speed?: 'slow' | 'fast'
}

const AtomLoader: React.FC<AtomLoaderProps> = ({ size = 'sm', speed = 'slow' }) => {
    const sizePx = size === 'lg' ? 50 : size === 'sm' ? 30 : 25
    const blurSize = sizePx / 3

    return (
        <div className="relative flex justify-center items-center">
            <div
                className="absolute rounded-full bg-primary animate-pulse-size blur-sm"
                style={{
                    width: blurSize,
                    height: blurSize,
                }}
            ></div>
            <div
                className={`loader ${speed === 'slow' ? 'animate-[l2_9s_infinite_linear]' : 'animate-[l2_3s_infinite_linear]'}`}
                style={{ width: sizePx, height: sizePx / 2 }}
            ></div>
        </div>
    )
}

export default AtomLoader
