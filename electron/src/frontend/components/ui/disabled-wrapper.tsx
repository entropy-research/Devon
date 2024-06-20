import React from 'react'

interface DisabledWrapperProps extends React.HTMLAttributes<HTMLDivElement> {
    disabled: boolean
    children: React.ReactNode
}

const DisabledWrapper: React.FC<DisabledWrapperProps> = ({
    disabled,
    children,
    className,
    ...props
}) => {
    const combinedClassName = `${disabled ? 'pointer-events-none opacity-50' : ''} ${className || ''}`

    return (
        <div className={combinedClassName.trim()} {...props}>
            {children}
        </div>
    )
}

export default DisabledWrapper
