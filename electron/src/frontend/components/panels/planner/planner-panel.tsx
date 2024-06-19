import { PlannerTextarea } from '@/components/ui/textarea'

export default function PlannerPanel() {
    return (
        <div className="flex flex-col h-full min-w-[400px] w-[450px] rounded-lg pb-7">
            <p className="text-lg font-semibold mb-3">Devon&apos;s Planner</p>
            <PlannerTextarea />
        </div>
    )
}
