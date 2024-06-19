import { useState } from 'react'
import { Check, ChevronsUpDown } from 'lucide-react'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
} from '@/components/ui/command'
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from '@/components/ui/popover'

export type ComboboxItem = {
    value: string
    label: string
}

const Combobox = ({
    items,
    searchBar = false,
    itemType,
    className,
    selectedItem,
    setSelectedItem,
}: {
    items: ComboboxItem[]
    searchBar?: boolean
    itemType?: string
    className?: string
    selectedItem: ComboboxItem
    setSelectedItem: (value: unknown) => void
}) => {
    const [open, setOpen] = useState(false)

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <Button
                    variant="outline-thin"
                    role="combobox"
                    aria-expanded={open}
                    className={`w-[200px] justify-between ${className}`}
                >
                    {selectedItem
                        ? items.find(i => i.value === selectedItem.value)?.label
                        : `Select${' ' + itemType}...`}
                    <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[200px] p-0">
                <Command>
                    {searchBar && (
                        <CommandInput
                            placeholder={`Search${' ' + itemType}...`}
                        />
                    )}
                    <CommandEmpty className="pt-2 pb-0 px-4">
                        None found
                    </CommandEmpty>
                    <CommandList>
                        <CommandGroup>
                            {items.map(i => (
                                <CommandItem
                                    key={i.value}
                                    value={i.value}
                                    onSelect={currentValue => {
                                        setSelectedItem(i)
                                        setOpen(false)
                                    }}
                                >
                                    <Check
                                        className={cn(
                                            'mr-2 h-4 w-4',
                                            selectedItem.value === i.value
                                                ? 'opacity-100'
                                                : 'opacity-0'
                                        )}
                                    />
                                    {i.label}
                                </CommandItem>
                            ))}
                        </CommandGroup>
                    </CommandList>
                </Command>
            </PopoverContent>
        </Popover>
    )
}

export default Combobox
