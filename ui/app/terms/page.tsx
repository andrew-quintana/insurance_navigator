import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function TermsPage() {
  return (
    <div className="flex-1 bg-gradient-to-b from-cream-50 to-white p-4">
      <div className="container mx-auto max-w-3xl bg-white rounded-xl shadow-sm p-8 my-8">
        <h1 className="text-3xl font-bold text-teal-800 mb-6">Terms of Service</h1>
        <p className="text-teal-700 mb-4">This is a placeholder for the Medicare Navigator Terms of Service.</p>
        <p className="text-teal-700 mb-8">The complete terms will be added here.</p>
        <Link href="/">
          <Button variant="outline" className="text-teal-700 border-teal-700">
            Return to Home
          </Button>
        </Link>
      </div>
    </div>
  )
}
