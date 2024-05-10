import ElectronStore from 'electron-store'
import { Message, StoreSchema } from './types'

export function addMessageToHistory(
  store: ElectronStore<StoreSchema>,
  message: Message
) {
  const currentHistory: Message[] = store.get('conversationHistory')
  currentHistory.push(message)
  store.set('conversationHistory', currentHistory)
}

export function getConversationHistory(
  store: ElectronStore<StoreSchema>
): Message[] {
  return store.get('conversationHistory')
}
