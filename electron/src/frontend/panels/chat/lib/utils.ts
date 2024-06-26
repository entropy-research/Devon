export function parseFileDiff(input: string): {
    path: string
    language: string
    searchContent: string
    replaceContent: string
} {
    const lines = input.trim().split('\n')
    let path = ''
    let language = ''
    let searchContent = ''
    let replaceContent = ''
    let inSearch = false
    let inReplace = false

    if (lines.length > 0 && lines[0].startsWith('```')) {
        language = lines[0].slice(3).trim()
        lines.shift()
    } else {
        // First line is the file name
        path = lines[0].trim()
        lines.shift()
    }

    for (let line of lines) {
        if (line.includes('<<<<<<< SEARCH')) {
            inSearch = true
            continue
        } else if (line.includes('=======')) {
            inSearch = false
            inReplace = true
            continue
        } else if (line.includes('>>>>>>> REPLACE')) {
            inReplace = false
            continue
        }

        if (inSearch) {
            searchContent += line + '\n'
        } else if (inReplace) {
            replaceContent += line + '\n'
        }
    }

    return {
        path: path,
        language,
        searchContent: searchContent.trim(),
        replaceContent: replaceContent.trim(),
    }
}
