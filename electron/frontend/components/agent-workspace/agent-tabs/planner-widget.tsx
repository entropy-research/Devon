import { PlannerTextarea } from '@/components/ui/textarea'

export default function PlannerWidget() {
    return (
        <div className="flex flex-col h-full min-w-[400px] w-[450px] rounded-lg pb-5">
            <p className="text-lg font-semibold mb-4">Devon&apos;s Planner</p>
            <PlannerTextarea />
        </div>
    )
}
