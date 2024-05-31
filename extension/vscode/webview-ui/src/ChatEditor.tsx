import React, { useEffect, useRef, useState } from 'react';
// @ts-ignore
import { EditorContent, useEditor } from '@tiptap/react';
// @ts-ignore
import StarterKit from '@tiptap/starter-kit';
import { vscode } from './vscode';

interface ChatEditorProps {
  onSendMessage: (message: string) => void;
  status: string;
  eventState: any;
}

const ChatEditor: React.FC<ChatEditorProps> = ({ onSendMessage, status, eventState }) => {
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

  return (
    <div>
      <EditorContent editor={editor} />
      <div>
        {status}
        {/* {eventState.modelLoading ? <Spinner type="simpleDots" /> : <></>} */}
      </div>
      <button onClick={handleSendMessage}>Send</button>
    </div>
  );
};

export default ChatEditor;