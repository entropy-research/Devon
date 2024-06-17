import React from 'react'
import './bouncing-dots.css'


const BouncingDots: React.FC = () => {
    const sizePx = 3.5 

    return (
        <div className="relative flex items-end w-9 justify-center pb-2">
            <div
                className="dot-typing"
                style={{ width: sizePx, height: sizePx }}
            ></div>
        </div>
    )
}

export default BouncingDots
