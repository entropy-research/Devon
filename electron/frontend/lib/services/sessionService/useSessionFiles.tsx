import { useEffect, useState } from 'react'
import { fetchSessionState } from '@/lib/services/sessionService/sessionService'
import { useBackendUrl } from '@/contexts/BackendUrlContext'
import { File } from '@/lib/types'

const boilerplateFile = {
    id: 'main.py',
    name: 'main.py',
    path: 'main.py',
    language: 'python',
    value: {
        lines: `# Welcome to Devon!\n`,
    },
}

const boilerplateFile2 = {
    id: 'hello.py',
    name: 'hello.py',
    path: 'hello.py',
    language: 'python',
    value: {
        lines: `# Hello world!\n`,
    },
}

const useSessionFiles = chatId => {
    const [files, setFiles] = useState<File[]>([])
    const [selectedFileId, setSelectedFileId] = useState<string>('')
    const { backendUrl } = useBackendUrl()

    useEffect(() => {
        let intervalId

        async function getSessionState() {
            try {
                const res = await fetchSessionState(backendUrl, chatId)
                if (!res || !res.editor || !res.editor.files) return
                const editor = res.editor
                const f = editor.files
                const _files: File[] = []

                for (let key in f) {
                    if (f.hasOwnProperty(key)) {
                        const fileName = key.split('/').pop() ?? 'unnamed_file'
                        _files.push({
                            id: key,
                            name: fileName,
                            path: key,
                            language: mapLanguage(fileName),
                            value: f[key],
                        })
                    }
                }
                if (_files.length === 0) {
                    _files.push(boilerplateFile)
                    _files.push(boilerplateFile2)
                }
                setFiles(_files)
                if (
                    !selectedFileId ||
                    !_files.find(f => f.id === selectedFileId)
                ) {
                    setSelectedFileId(_files[0].id)
                }
            } catch (error) {
                console.error('Error fetching session state:', error)
            }
        }

        getSessionState()
        intervalId = setInterval(getSessionState, 2000)
        return () => clearInterval(intervalId)
    }, [chatId, selectedFileId])

    return { files, selectedFileId, setSelectedFileId }
}

export default useSessionFiles

// https://github.com/microsoft/monaco-editor/tree/main/src/basic-languages
const extensionToLanguageMap: { [key: string]: string } = {
    abap: 'abap',
    cls: 'apex',
    azcli: 'azcli',
    bat: 'bat',
    cmd: 'bat',
    bicep: 'bicep',
    mligo: 'cameligo',
    clj: 'clojure',
    cljs: 'clojure',
    cljc: 'clojure',
    coffee: 'coffee',
    c: 'cpp',
    cpp: 'cpp',
    h: 'cpp',
    hpp: 'cpp',
    cs: 'csharp',
    csx: 'csharp',
    csp: 'csp',
    css: 'css',
    cypher: 'cypher',
    dart: 'dart',
    dockerfile: 'dockerfile',
    ecl: 'ecl',
    ex: 'elixir',
    exs: 'elixir',
    flow: 'flow9',
    ftl: 'freemarker2',
    fs: 'fsharp',
    fsi: 'fsharp',
    fsx: 'fsharp',
    fsscript: 'fsharp',
    go: 'go',
    graphql: 'graphql',
    handlebars: 'handlebars',
    hbs: 'handlebars',
    tf: 'hcl',
    tfvars: 'hcl',
    hcl: 'hcl',
    html: 'html',
    htm: 'html',
    ini: 'ini',
    java: 'java',
    js: 'javascript',
    mjs: 'javascript',
    cjs: 'javascript',
    jsx: 'javascript',
    jl: 'julia',
    kt: 'kotlin',
    kts: 'kotlin',
    less: 'less',
    lex: 'lexon',
    liquid: 'liquid',
    lua: 'lua',
    m3: 'm3',
    md: 'markdown',
    markdown: 'markdown',
    mdx: 'mdx',
    asm: 'mips',
    dax: 'msdax',
    mysql: 'mysql',
    objc: 'objective-c',
    pas: 'pascal',
    pp: 'pascal',
    ligo: 'pascaligo',
    pl: 'perl',
    pm: 'perl',
    pgsql: 'pgsql',
    php: 'php',
    p: 'pla',
    atd: 'postiats',
    pq: 'powerquery',
    pqm: 'powerquery',
    ps1: 'powershell',
    psm1: 'powershell',
    proto: 'protobuf',
    jade: 'pug',
    pug: 'pug',
    py: 'python',
    qs: 'qsharp',
    r: 'r',
    cshtml: 'razor',
    redis: 'redis',
    redshift: 'redshift',
    rst: 'restructuredtext',
    rb: 'ruby',
    rs: 'rust',
    sb: 'sb',
    scala: 'scala',
    scm: 'scheme',
    scss: 'scss',
    sh: 'shell',
    sol: 'solidity',
    aes: 'sophia',
    rq: 'sparql',
    sql: 'sql',
    st: 'st',
    swift: 'swift',
    sv: 'systemverilog',
    svh: 'systemverilog',
    tcl: 'tcl',
    test: 'test',
    twig: 'twig',
    ts: 'typescript',
    tsx: 'typescript',
    spec: 'typespec',
    vb: 'vb',
    wgsl: 'wgsl',
    xml: 'xml',
    yaml: 'yaml',
    yml: 'yaml',
}

function mapLanguage(filename: string): string {
    const extension = filename.split('.').pop()?.toLowerCase()
    return extension
        ? extensionToLanguageMap[extension] || 'plaintext'
        : 'plaintext'
}
