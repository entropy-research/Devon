import React, { useState, useCallback, useMemo } from 'react';
import { Bot } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Icon } from '@iconify/react';
import { useToast } from '@/components/ui/use-toast';

const EditorPanelHeader = ({ path }: { path: string }) => {
    const { toast } = useToast();
    const [vscodeTooltipOpen, setVscodeTooltipOpen] = useState(false);

    const vscodeProjectLink = useMemo(() => `vscode://file/${path}`, [path]);

    const openVSCode = useCallback(() => {
        window.open(vscodeProjectLink, '_self');
        setVscodeTooltipOpen(false);
    }, [vscodeProjectLink]);

    const handleTriggerClick = useCallback(() => {
        openVSCode();
        setVscodeTooltipOpen(false);
    }, [openVSCode]);

    return (
        <div className="w-full border-b border-outlinecolor flex justify-center py-1 relative group">
            <div className="flex space-x-2 ml-2 mr-4 absolute left-1 top-[11px] opacity-80">
                <div className="w-[9px] h-[9px] bg-red-500 rounded-full"></div>
                <div className="w-[9px] h-[9px] bg-yellow-400 rounded-full"></div>
                <div className="w-[9px] h-[9px] bg-green-500 rounded-full"></div>
            </div>
            <button
                onClick={() =>
                    toast({
                        title: 'Hey! ~ Devon waves at you ~ 👋',
                    })
                }
                className="group smooth-hover bg-night px-[100px] border border-outlinecolor rounded-md my-1 flex gap-[5px] items-center"
            >
                <Bot
                    size={12}
                    className="group-hover:text-white text-neutral-400 mb-[2px] -ml-2 transition duration-300"
                />
                <p className="group-hover:text-white text-[0.8rem] text-neutral-400 transition duration-300">
                    Devon
                </p>
            </button>
            <div className="absolute right-2 mt-1 group">
                <TooltipProvider>
                    <Tooltip
                        open={vscodeTooltipOpen}
                        onOpenChange={setVscodeTooltipOpen}
                    >
                        <TooltipTrigger asChild>
                            <a onClick={handleTriggerClick}>
                                <Icon
                                    icon="vscode-icons:file-type-vscode"
                                    className="h-[16px] w-[16px] opacity-0 transition-opacity duration-300 group-hover:opacity-90 hover:cursor-pointer"
                                />
                            </a>
                        </TooltipTrigger>
                        <TooltipContent
                            className="hover:cursor-pointer hover:border-primary smooth-hover"
                            onClick={openVSCode}
                        >
                            <p>Open in VSCode</p>
                        </TooltipContent>
                    </Tooltip>
                </TooltipProvider>
            </div>
        </div>
    );
};

export default React.memo(EditorPanelHeader);