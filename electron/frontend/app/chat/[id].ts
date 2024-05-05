import { getChatById } from '@/lib/services/chatService'

export default async function handler(req, res) {
    const { id } = req.query
    try {
        const chat = await getChatById(id) // Server-side function that accesses your database
        if (chat) {
            res.status(200).json({ success: true, data: chat })
        } else {
            res.status(404).json({ success: false, message: 'Chat not found' })
        }
    } catch (error) {
        res.status(500).json({ success: false, message: error.message })
    }
}
