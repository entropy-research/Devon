export default function TimelineWidget({ className }) {
    return (
        // <div className="h-full mt-[120px] flex w-full">
        //     <div className="bg-batman w-full min-w-[300px] h-[500px] p-5 rounded-lg">
        //         <p className="text-lg font-semibold">Timeline</p>
        //     </div>
        // </div>
        <div className={`h-full pb-7 pr-5 ${className}`}>
            {/* <p className="text-lg font-semibold mb-3">Timeline</p> */}
            <div className="bg-batman w-full min-w-[250px] h-full p-5 rounded-lg border-input border"></div>
        </div>
    )
}
