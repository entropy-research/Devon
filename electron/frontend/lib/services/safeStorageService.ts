import { useEffect } from 'react'

export const useSafeStorage = () => {
    useEffect(() => {
        // Loads the encrypted data from the store
        loadData()
    }, [])

    const decryptText = async encryptedText => {
        const decrypted = await window.api.invoke('decrypt-data', encryptedText)
        return decrypted
    }

    const loadData = async () => {
        const response = await window.api.invoke('load-data')
        console.log("load data",response)
        if (response.success) {
            if (response.data) {
                return JSON.parse(response.data)
            }
            return {}
        } else {
            console.error('Error:', response.message)
        }
    }

    const saveData = async data => {
        const plainText = JSON.stringify(data)
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

    const addApiKey = async (keyName, keyValue) => {
        const data = (await loadData()) || {}
        data[keyName] = keyValue
        await saveData(data)
    }

    const getApiKey = async keyName => {
        const data = await loadData()
        console.log("data", data)
        return data ? data[keyName] : null
    }

    const removeApiKey = async keyName => {
        const data = await loadData()
        if (data && data[keyName]) {
            delete data[keyName]
            await saveData(data)
        }
    }

    return {
        decryptText,
        loadData,
        saveData,
        deleteData,
        checkHasEncryptedData,
        addApiKey,
        getApiKey,
        removeApiKey,
    }
}
