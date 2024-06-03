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
        lines: `# Welcome to Devon!\n
"""
         __________
       /  ========  \\
      | ___________ |
      | | >_      | |
      | |         | |    let's get started!
      | |_________| |________________________
      \\=____________/             — devon    )
      / """"""""""" \\                       /
     / ::::::::::::: \\                  =D-'
    (_________________)

"""`,
    },
} // https://www.asciiart.eu/computers/computers

const boilerplateFile2 = {
    id: 'hello.py',
    name: 'hello.py',
    path: 'hello.py',
    language: 'python',
    value: {
        lines: `# Start by giving me a task in the chat!\n\n# This is my editor :)
def hello_world():
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
`,
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
                            icon: mapIcon(fileName),
                        })
                    }
                }
                if (_files.length === 0) {
                    _files.push({
                        ...boilerplateFile,
                        language: mapLanguage(boilerplateFile.path),
                        icon: mapIcon(boilerplateFile.path),
                    })
                    _files.push({
                        ...boilerplateFile2,
                        language: mapLanguage(boilerplateFile2.path),
                        icon: mapIcon(boilerplateFile2.path),
                    })
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

function mapIcon(filename: string): string | undefined {
    const extension = filename.split('.').pop()?.toLowerCase()
    return extension ? extensionToIconMap[extension] : undefined
}

// https://iconify.design/docs/icon-components/react/
const extensionToIconMap: { [key: string]: string | undefined } = {
    abap: 'file-icons:abap',
    cls: 'file-icons:apex',
    azcli: 'vscode-icons:file-type-azcli',
    bat: 'vscode-icons:file-type-bat',
    cmd: 'vscode-icons:file-type-bat',
    bicep: 'vscode-icons:file-type-bicep',
    mligo: 'file-icons:cameligo',
    clj: 'file-icons:clojure',
    cljs: 'file-icons:clojurescript',
    cljc: 'file-icons:clojure',
    coffee: 'vscode-icons:file-type-coffeescript',
    c: 'vscode-icons:file-type-c',
    cpp: 'vscode-icons:file-type-cpp',
    h: 'vscode-icons:file-type-cpp',
    hpp: 'vscode-icons:file-type-cpp',
    cs: 'vscode-icons:file-type-csharp',
    csx: 'vscode-icons:file-type-csharp',
    csp: 'file-icons:csp',
    css: 'vscode-icons:file-type-css',
    cypher: 'file-icons:cypher',
    dart: 'vscode-icons:file-type-dart',
    dockerfile: 'vscode-icons:file-type-docker',
    ecl: 'file-icons:ecl',
    ex: 'vscode-icons:file-type-elixir',
    exs: 'vscode-icons:file-type-elixir',
    flow: 'file-icons:flow',
    ftl: 'file-icons:freemarker',
    fs: 'vscode-icons:file-type-fsharp',
    fsi: 'vscode-icons:file-type-fsharp',
    fsx: 'vscode-icons:file-type-fsharp',
    fsscript: 'vscode-icons:file-type-fsharp',
    go: 'vscode-icons:file-type-go',
    graphql: 'vscode-icons:file-type-graphql',
    handlebars: 'vscode-icons:file-type-handlebars',
    hbs: 'vscode-icons:file-type-handlebars',
    tf: 'file-icons:terraform',
    tfvars: 'file-icons:terraform',
    hcl: 'file-icons:hcl',
    html: 'vscode-icons:file-type-html',
    htm: 'vscode-icons:file-type-html',
    ini: 'vscode-icons:file-type-settings',
    java: 'vscode-icons:file-type-java',
    js: 'vscode-icons:file-type-js-official',
    mjs: 'vscode-icons:file-type-js-official',
    cjs: 'vscode-icons:file-type-js-official',
    jsx: 'vscode-icons:file-type-reactjs',
    jl: 'file-icons:julia',
    kt: 'vscode-icons:file-type-kotlin',
    kts: 'vscode-icons:file-type-kotlin',
    less: 'vscode-icons:file-type-less',
    lex: 'file-icons:lexon',
    liquid: 'vscode-icons:file-type-liquid',
    lua: 'vscode-icons:file-type-lua',
    m3: 'file-icons:m3',
    md: 'vscode-icons:file-type-markdown',
    markdown: 'vscode-icons:file-type-markdown',
    mdx: 'vscode-icons:file-type-mdx',
    asm: 'file-icons:mips',
    dax: 'file-icons:dax',
    mysql: 'vscode-icons:file-type-mysql',
    objc: 'vscode-icons:file-type-objectivec',
    pas: 'file-icons:pascal',
    pp: 'file-icons:pascal',
    ligo: 'file-icons:ligo',
    pl: 'vscode-icons:file-type-perl',
    pm: 'vscode-icons:file-type-perl',
    pgsql: 'file-icons:pgsql',
    php: 'vscode-icons:file-type-php',
    p: 'file-icons:pla',
    atd: 'file-icons:postiats',
    pq: 'file-icons:powerquery',
    pqm: 'file-icons:powerquery',
    ps1: 'vscode-icons:file-type-powershell',
    psm1: 'vscode-icons:file-type-powershell',
    proto: 'file-icons:protobuf',
    jade: 'file-icons:pug',
    pug: 'file-icons:pug',
    py: 'vscode-icons:file-type-python',
    qs: 'file-icons:qsharp',
    r: 'vscode-icons:file-type-r',
    cshtml: 'vscode-icons:file-type-razor',
    redis: 'file-icons:redis',
    redshift: 'file-icons:redshift',
    rst: 'vscode-icons:file-type-restructuredtext',
    rb: 'vscode-icons:file-type-ruby',
    rs: 'vscode-icons:file-type-rust',
    sb: 'file-icons:sb',
    scala: 'vscode-icons:file-type-scala',
    scm: 'file-icons:scheme',
    scss: 'vscode-icons:file-type-scss',
    sh: 'vscode-icons:file-type-shell',
    sol: 'file-icons:solidity',
    aes: 'file-icons:sophia',
    rq: 'file-icons:sparql',
    sql: 'vscode-icons:file-type-sql',
    st: 'file-icons:st',
    swift: 'vscode-icons:file-type-swift',
    sv: 'file-icons:verilog',
    svh: 'file-icons:verilog',
    tcl: 'file-icons:tcl',
    test: 'file-icons:test',
    twig: 'file-icons:twig',
    ts: 'vscode-icons:file-type-typescript-official',
    tsx: 'vscode-icons:file-type-typescript-official',
    spec: 'file-icons:typespec',
    vb: 'vscode-icons:file-type-visualstudio',
    wgsl: 'file-icons:wgsl',
    xml: 'vscode-icons:file-type-xml',
    yaml: 'vscode-icons:file-type-yaml',
    yml: 'vscode-icons:file-type-yaml',
}
