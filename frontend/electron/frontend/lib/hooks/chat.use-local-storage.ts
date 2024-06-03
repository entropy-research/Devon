'use client'
import { useEffect, useState } from 'react'

export const useLocalStorageOld = <T>(
    key: string,
    initialValue: T
): [T, (value: T) => void, () => void] => {
    const [storedValue, setStoredValue] = useState(() => {
        // Retrieve from localStorage and handle SSR (Server Side Rendering) if necessary
        try {
            const item = localStorage.getItem(key)
            return item ? JSON.parse(item) : initialValue
        } catch (error) {
            console.log('Error reading localStorage key “' + key + '”: ', error)
            return initialValue
        }
    })

    useEffect(() => {
        // Initialize or re-initialize if the key changes
        const item = localStorage.getItem(key)
        if (item && item !== 'undefined') {
            setStoredValue(JSON.parse(item))
        }
    }, [key])

    const setValue = (value: T) => {
        try {
            // Save state
            setStoredValue(value)
            // Save to localStorage
            localStorage.setItem(key, JSON.stringify(value))
        } catch (error) {
            console.log(
                'Error saving to localStorage key “' + key + '”: ',
                error
            )
        }
    }

    const clearValue = () => {
        try {
            // Clear from localStorage
            localStorage.removeItem(key)
            // Reset local state
            setStoredValue(initialValue)
        } catch (error) {
            console.log(
                'Error removing localStorage key “' + key + '”: ',
                error
            )
        }
    }

    return [storedValue, setValue, clearValue]
}

export const useLocalStorage = <T>(
    key: string,
    initialValue: T
): [T, (value: T) => void, () => void] => {
    const [storedValue, setStoredValue] = useState(initialValue)

    useEffect(() => {
        // Retrieve from localStorage
        const item = window.localStorage.getItem(key)
        if (item && item !== 'undefined') {
            setStoredValue(JSON.parse(item))
        }
    }, [key])

    const setValue = (value: T) => {
        // Save state
        setStoredValue(value)
        // Save to localStorage
        window.localStorage.setItem(key, JSON.stringify(value))
    }

    const clearValue = () => {
        try {
            // Clear from localStorage
            localStorage.removeItem(key)
            // Reset local state
            setStoredValue(initialValue)
        } catch (error) {
            console.log(
                'Error removing localStorage key “' + key + '”: ',
                error
            )
        }
    }
    return [storedValue, setValue, clearValue]
}
