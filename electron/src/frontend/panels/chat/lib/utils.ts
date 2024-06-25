export function parseFileDiff(input: string): {
    filename: string
    language: string
    searchContent: string
    replaceContent: string
} {
    const lines = input.trim().split('\n')
    let filename = ''
    let language = ''
    let searchContent = ''
    let replaceContent = ''
    let inSearch = false
    let inReplace = false

    // First line is the file name
    filename = lines[0].trim()
    lines.shift()

    // Extract language from the first line
    if (lines.length > 0 && lines[0].startsWith('```')) {
        language = lines[0].slice(3).trim()
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
        filename,
        language,
        searchContent: searchContent.trim(),
        replaceContent: replaceContent.trim(),
    }
}
