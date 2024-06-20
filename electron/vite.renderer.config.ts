import type { ConfigEnv, UserConfig } from 'vite'
import { defineConfig } from 'vite'
import { pluginExposeRenderer } from './vite.base.config'
import react from '@vitejs/plugin-react'
import * as path from 'path'

// https://vitejs.dev/config
export default defineConfig(env => {
    const forgeEnv = env as ConfigEnv<'renderer'>
    const { root, mode, forgeConfigSelf } = forgeEnv
    const name = forgeConfigSelf.name ?? ''

    return {
        root,
        mode,
        base: './',
        build: {
            outDir: `.vite/renderer/${name}`,
        },
        server: {
            port: 3000,
        },
        plugins: [pluginExposeRenderer(name), react()],
        resolve: {
            preserveSymlinks: true,
            alias: [
                {
                    find: '@',
                    replacement: path.resolve(__dirname, 'src/frontend'),
                },
            ],
        },
        clearScreen: false,
    } as UserConfig
})
