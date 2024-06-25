// Define the type for a single mapping entry
interface Mapping {
    language: string
    icon: string
}

// Define the type for the mappings object
interface Mappings {
    [key: string]: Mapping
}

/* Mapping data structure
Languages:
- https://github.com/microsoft/monaco-editor/tree/main/src/basic-languages

Icons:
- Docs: https://iconify.design/docs/icon-components/react/
- Directory: https://icon-sets.iconify.design/
*/
const mappings: Mappings = {
    abap: { language: 'abap', icon: 'file-icons:abap' },
    cls: { language: 'apex', icon: 'file-icons:apex' },
    azcli: { language: 'azcli', icon: 'vscode-icons:file-type-azcli' },
    bat: { language: 'bat', icon: 'vscode-icons:file-type-bat' },
    cmd: { language: 'bat', icon: 'vscode-icons:file-type-bat' },
    bicep: { language: 'bicep', icon: 'vscode-icons:file-type-bicep' },
    mligo: { language: 'cameligo', icon: 'file-icons:cameligo' },
    clj: { language: 'clojure', icon: 'file-icons:clojure' },
    cljs: { language: 'clojure', icon: 'file-icons:clojurescript' },
    cljc: { language: 'clojure', icon: 'file-icons:clojure' },
    coffee: { language: 'coffee', icon: 'vscode-icons:file-type-coffeescript' },
    c: { language: 'cpp', icon: 'vscode-icons:file-type-c' },
    cpp: { language: 'cpp', icon: 'vscode-icons:file-type-cpp' },
    h: { language: 'cpp', icon: 'vscode-icons:file-type-cpp' },
    hpp: { language: 'cpp', icon: 'vscode-icons:file-type-cpp' },
    cs: { language: 'csharp', icon: 'vscode-icons:file-type-csharp' },
    csx: { language: 'csharp', icon: 'vscode-icons:file-type-csharp' },
    csp: { language: 'csp', icon: 'file-icons:csp' },
    css: { language: 'css', icon: 'vscode-icons:file-type-css' },
    cypher: { language: 'cypher', icon: 'file-icons:cypher' },
    dart: { language: 'dart', icon: 'vscode-icons:file-type-dart' },
    dockerfile: {
        language: 'dockerfile',
        icon: 'vscode-icons:file-type-docker',
    },
    ecl: { language: 'ecl', icon: 'file-icons:ecl' },
    ex: { language: 'elixir', icon: 'vscode-icons:file-type-elixir' },
    exs: { language: 'elixir', icon: 'vscode-icons:file-type-elixir' },
    flow: { language: 'flow9', icon: 'file-icons:flow' },
    ftl: { language: 'freemarker2', icon: 'file-icons:freemarker' },
    fs: { language: 'fsharp', icon: 'vscode-icons:file-type-fsharp' },
    fsi: { language: 'fsharp', icon: 'vscode-icons:file-type-fsharp' },
    fsx: { language: 'fsharp', icon: 'vscode-icons:file-type-fsharp' },
    fsscript: { language: 'fsharp', icon: 'vscode-icons:file-type-fsharp' },
    go: { language: 'go', icon: 'vscode-icons:file-type-go' },
    graphql: { language: 'graphql', icon: 'vscode-icons:file-type-graphql' },
    handlebars: {
        language: 'handlebars',
        icon: 'vscode-icons:file-type-handlebars',
    },
    hbs: { language: 'handlebars', icon: 'vscode-icons:file-type-handlebars' },
    tf: { language: 'hcl', icon: 'file-icons:terraform' },
    tfvars: { language: 'hcl', icon: 'file-icons:terraform' },
    hcl: { language: 'hcl', icon: 'file-icons:hcl' },
    html: { language: 'html', icon: 'vscode-icons:file-type-html' },
    htm: { language: 'html', icon: 'vscode-icons:file-type-html' },
    ini: { language: 'ini', icon: 'vscode-icons:file-type-settings' },
    java: { language: 'java', icon: 'vscode-icons:file-type-java' },
    js: { language: 'javascript', icon: 'vscode-icons:file-type-js-official' },
    mjs: { language: 'javascript', icon: 'vscode-icons:file-type-js-official' },
    cjs: { language: 'javascript', icon: 'vscode-icons:file-type-js-official' },
    jsx: { language: 'javascript', icon: 'vscode-icons:file-type-reactjs' },
    jl: { language: 'julia', icon: 'file-icons:julia' },
    kt: { language: 'kotlin', icon: 'vscode-icons:file-type-kotlin' },
    kts: { language: 'kotlin', icon: 'vscode-icons:file-type-kotlin' },
    less: { language: 'less', icon: 'vscode-icons:file-type-less' },
    lex: { language: 'lexon', icon: 'file-icons:lexon' },
    liquid: { language: 'liquid', icon: 'vscode-icons:file-type-liquid' },
    lua: { language: 'lua', icon: 'vscode-icons:file-type-lua' },
    m3: { language: 'm3', icon: 'file-icons:m3' },
    md: { language: 'markdown', icon: 'vscode-icons:file-type-markdown' },
    markdown: { language: 'markdown', icon: 'vscode-icons:file-type-markdown' },
    mdx: { language: 'mdx', icon: 'vscode-icons:file-type-mdx' },
    asm: { language: 'mips', icon: 'file-icons:mips' },
    dax: { language: 'msdax', icon: 'file-icons:dax' },
    mysql: { language: 'mysql', icon: 'vscode-icons:file-type-mysql' },
    objc: {
        language: 'objective-c',
        icon: 'vscode-icons:file-type-objectivec',
    },
    pas: { language: 'pascal', icon: 'file-icons:pascal' },
    pp: { language: 'pascal', icon: 'file-icons:pascal' },
    ligo: { language: 'pascaligo', icon: 'file-icons:ligo' },
    pl: { language: 'perl', icon: 'vscode-icons:file-type-perl' },
    pm: { language: 'perl', icon: 'vscode-icons:file-type-perl' },
    pgsql: { language: 'pgsql', icon: 'file-icons:pgsql' },
    php: { language: 'php', icon: 'vscode-icons:file-type-php' },
    p: { language: 'pla', icon: 'file-icons:pla' },
    atd: { language: 'postiats', icon: 'file-icons:postiats' },
    pq: { language: 'powerquery', icon: 'file-icons:powerquery' },
    pqm: { language: 'powerquery', icon: 'file-icons:powerquery' },
    ps1: { language: 'powershell', icon: 'vscode-icons:file-type-powershell' },
    psm1: { language: 'powershell', icon: 'vscode-icons:file-type-powershell' },
    proto: { language: 'protobuf', icon: 'file-icons:protobuf' },
    jade: { language: 'pug', icon: 'file-icons:pug' },
    pug: { language: 'pug', icon: 'file-icons:pug' },
    py: { language: 'python', icon: 'vscode-icons:file-type-python' },
    qs: { language: 'qsharp', icon: 'file-icons:qsharp' },
    r: { language: 'r', icon: 'vscode-icons:file-type-r' },
    cshtml: { language: 'razor', icon: 'vscode-icons:file-type-razor' },
    redis: { language: 'redis', icon: 'file-icons:redis' },
    redshift: { language: 'redshift', icon: 'file-icons:redshift' },
    rst: {
        language: 'restructuredtext',
        icon: 'vscode-icons:file-type-restructuredtext',
    },
    rb: { language: 'ruby', icon: 'vscode-icons:file-type-ruby' },
    rs: { language: 'rust', icon: 'vscode-icons:file-type-rust' },
    sb: { language: 'sb', icon: 'file-icons:sb' },
    scala: { language: 'scala', icon: 'vscode-icons:file-type-scala' },
    scm: { language: 'scheme', icon: 'file-icons:scheme' },
    scss: { language: 'scss', icon: 'vscode-icons:file-type-scss' },
    sh: { language: 'shell', icon: 'vscode-icons:file-type-shell' },
    sol: { language: 'solidity', icon: 'file-icons:solidity' },
    aes: { language: 'sophia', icon: 'file-icons:sophia' },
    rq: { language: 'sparql', icon: 'file-icons:sparql' },
    sql: { language: 'sql', icon: 'vscode-icons:file-type-sql' },
    st: { language: 'st', icon: 'file-icons:st' },
    swift: { language: 'swift', icon: 'vscode-icons:file-type-swift' },
    sv: { language: 'systemverilog', icon: 'file-icons:verilog' },
    svh: { language: 'systemverilog', icon: 'file-icons:verilog' },
    tcl: { language: 'tcl', icon: 'file-icons:tcl' },
    test: { language: 'test', icon: 'file-icons:test' },
    twig: { language: 'twig', icon: 'file-icons:twig' },
    ts: {
        language: 'typescript',
        icon: 'vscode-icons:file-type-typescript-official',
    },
    tsx: {
        language: 'typescript',
        icon: 'vscode-icons:file-type-reactts',
    },
    spec: { language: 'typespec', icon: 'file-icons:typespec' },
    vb: { language: 'vb', icon: 'vscode-icons:file-type-visualstudio' },
    wgsl: { language: 'wgsl', icon: 'file-icons:wgsl' },
    xml: { language: 'xml', icon: 'vscode-icons:file-type-xml' },
    yaml: { language: 'yaml', icon: 'vscode-icons:file-type-yaml' },
    yml: { language: 'yaml', icon: 'vscode-icons:file-type-yaml' },
    ipynb: { language: 'jupyter', icon: 'vscode-icons:jupyter' },
    txt: { language: 'txt', icon: 'vscode-icons:file-type-text' },
    gitignore: { language: 'gitignore', icon: 'vscode-icons:file-type-git' },
    json: { language: 'json', icon: 'vscode-icons:file-type-json' },
    env: { language: 'dotenv', icon: 'vscode-icons:file-type-dotenv' },
}

// Function to get language from filename
export function getLanguageFromFilename(filename: string): string | null {
    const extension = filename.split('.').pop().toLowerCase()
    return getLanguageFromExtension(extension)
}

// Function to get icon from filename
export function getIconFromFilename(filename: string): string | null {
    const extension = filename.split('.').pop().toLowerCase()
    return getIconFromExtension(extension)
}

// Function to get language from extension
export function getLanguageFromExtension(extension: string): string | null {
    return mappings[extension]?.language || null
}

// Function to get icon from extension
export function getIconFromExtension(extension: string): string | null {
    return mappings[extension]?.icon || null
}

// Function to get icon from language
export function getIconFromLanguage(language: string): string | null {
    for (const key in mappings) {
        if (mappings[key].language === language) {
            return mappings[key].icon
        }
    }
    return null
}
