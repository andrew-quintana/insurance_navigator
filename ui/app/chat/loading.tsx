import { Loader2 } from "lucide-react"

export default function Loading() {
  return (
    <div className="min-h-screen bg-cream-50 flex items-center justify-center">
      <div className="flex flex-col items-center">
        <Loader2 className="h-12 w-12 text-teal-700 animate-spin" />
        <p className="mt-4 text-teal-800 font-medium">Loading Insurance Navigator...</p>
      </div>
    </div>
  )
}
