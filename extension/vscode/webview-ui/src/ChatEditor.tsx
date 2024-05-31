import React, { useEffect, useRef } from 'react';
// @ts-ignore
import { EditorContent, useEditor } from '@tiptap/react';
// @ts-ignore
import StarterKit from '@tiptap/starter-kit';
import { vscode } from './vscode';

interface ChatEditorProps {
  onSendMessage: (message: string) => void;
}

const ChatEditor: React.FC<ChatEditorProps> = ({ onSendMessage }) => {
  const editor = useEditor({
    extensions: [StarterKit],
    content: '',
  });

  const handleSendMessage = () => {
    if (editor && editor.getHTML() !== '<p></p>') {
      onSendMessage(editor.getHTML());
      editor.commands.clearContent();
    }
  };

  useEffect(() => {
    editor?.commands.focus();
  }, [editor]);

  useEffect(() => {
    console.log("starting server")
    
  }, [])

  return (
    <div>
      <EditorContent editor={editor} />
      <button onClick={() => vscode.postMessage({ command: 'startServer' })}>Send</button>
    </div>
  );
};

export default ChatEditor;
