#!/usr/bin/env node
const { spawn } = require('child_process')
const path = require('path')
const electronPath = require('electron') // Ensure Electron is installed as a dependency

const main = () => {
    const subprocess = spawn(electronPath, [path.join(__dirname, 'main.js')], {
        stdio: 'inherit',
    })
    subprocess.on('error', (err: any) => {
        console.error('Failed to start subprocess.', err)
    })

    subprocess.on('close', (code: any) => {
        console.log(`Electron process exited with code ${code}`)
    })
}

main()
