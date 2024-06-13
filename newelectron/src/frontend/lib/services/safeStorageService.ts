import { useEffect } from 'react'

export const useSafeStorage = () => {
    useEffect(() => {
        // Loads the encrypted data from the store
        loadData()
    }, [])

    const decryptText = async (encryptedText: string) => {
        //@ts-ignore
        const decrypted = await window.api.invoke('decrypt-data', encryptedText)
        return decrypted
    }

    const loadData = async () => {
        //@ts-ignore
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

    const saveData = async (data: any, reload: boolean = true) => {
        const plainText = JSON.stringify(data)
        //@ts-ignore
        const response = await window.api.invoke('save-data', plainText)
        if (reload) {
            window.location.reload()
        }
    }

    const deleteData = async () => {
        //@ts-ignore
        const response = await window.api.invoke('delete-encrypted-data')
        window.location.reload()
    }

    const checkHasEncryptedData = async () => {
        //@ts-ignore
        const response = await window.api.invoke('check-has-encrypted-data')
        return response.success
    }

    const addApiKey = async (keyName: string, keyValue: string, reload: boolean = true) => {
        const data = (await loadData()) || {}
        data[keyName] = keyValue
        await saveData(data, reload)
    }

    const getApiKey = async (keyName: string) => {
        const data = await loadData()
        console.log("data", data)
        return data ? data[keyName] : null
    }

    const removeApiKey = async (keyName: string) => {
        const data = await loadData()
        if (data && data[keyName]) {
            delete data[keyName]
            await saveData(data)
        }
    }

    const setUseModelName = async (modelName: string, reload: boolean = true) => {
        const data = await loadData()
        data.useModelName = modelName
        await saveData(data, reload)
    }

    const getUseModelName = async () => {
        const data = await loadData()
        return data.useModelName
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
        setUseModelName,
        getUseModelName,
    }
}
