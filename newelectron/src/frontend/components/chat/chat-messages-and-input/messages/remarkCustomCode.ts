import { visit } from 'unist-util-visit'

// Turn everything after <<< into code
export function remarkCustomCode() {
    console.log('Custom Remark plugin loaded')
    return tree => {
        visit(tree, 'text', node => {
            const { value } = node
            console.log('Processing node:', node)
            if (value.includes('<<<')) {
                console.log('Custom code block detected:', value)
                const codeBlocks = value.split('<<<')
                console.log('Split code blocks:', codeBlocks)
                const children: any = []

                if (codeBlocks.length > 1) {
                    children.push({
                        type: 'paragraph',
                        children: [{ type: 'text', value: codeBlocks[0] }],
                    })
                    children.push({ type: 'html', value: '<pre><code>' })
                    children.push({
                        type: 'text',
                        value: codeBlocks.slice(1).join('<<<'),
                    })
                    children.push({ type: 'html', value: '</code></pre>' })
                } else {
                    children.push({ type: 'text', value: codeBlocks[0] })
                }

                node.type = 'root'
                node.children = children
                console.log('Transformed node:', node)
            }
        })
    }
}
