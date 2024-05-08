import { useEffect } from 'react'

export const useSafeStorage = () => {
    useEffect(() => {
        // Loads in the key on load
        loadData()
    }, [])

    const decryptText = async encryptedText => {
        const decrypted = await window.api.invoke('decrypt-data', encryptedText)
        return decrypted
    }

    const loadData = async () => {
        const response = await window.api.invoke('load-data')
        if (response.success) {
            return response.data
        } else {
            // console.error('Error:', response.message)
        }
    }

    const saveData = async plainText => {
        const response = await window.api.invoke('save-data', plainText)
        window.location.reload()
    }

    const deleteData = async () => {
        const response = await window.api.invoke('delete-encrypted-data')
        window.location.reload()
    }

    const checkHasEncryptedData = async () => {
        const response = await window.api.invoke('check-has-encrypted-data')
        return response.success
    }

    return {
        decryptText,
        loadData,
        saveData,
        deleteData,
        checkHasEncryptedData,
    }
}
