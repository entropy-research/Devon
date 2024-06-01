import React from 'react'
import './atom.css' // Import the CSS file for the keyframes

interface AtomLoaderProps {
    size?: 'sm' | 'lg'
}

const AtomLoader: React.FC<AtomLoaderProps> = ({ size = 'sm' }) => {
    const sizePx = size === 'lg' ? 50 : 30
    const blurSize = sizePx / 3

    return (
        <div className="relative flex justify-center items-center">
            <div
                className="absolute rounded-full bg-primary animate-pulse blur-sm"
                style={{
                    width: blurSize,
                    height: blurSize,
                }}
            ></div>
            <div
                className="loader"
                style={{ width: sizePx, height: sizePx / 2 }}
            ></div>
        </div>
    )
}

export default AtomLoader
