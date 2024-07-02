import { Model } from './types'

export const models: Model[] = [
    {
        id: 'claude-3-5-sonnet',
        name: 'Claude 3.5 Sonnet',
        company: 'Anthropic',
        apiKeyUrl: 'https://console.anthropic.com/settings/keys',
    },
    {
        id: 'gpt4-o',
        name: 'GPT4-o',
        company: 'OpenAI',
        apiKeyUrl: 'https://platform.openai.com/api-keys',
    },
    // {
    //     id: 'llama-3-70b',
    //     name: 'Groq Llama 3 70B',
    //     company: 'Groq',
    // },
    // {
    //     id: 'ollama/deepseek-coder:6.7b',
    //     name: 'Ollama Deepseek 6.7b',
    //     company: 'Ollama',
    // },
    // {
    //     id: 'custom',
    //     name: 'Custom',
    //     company: 'Custom',
    //     comingSoon: true,
    // },
]
