import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { ArrowLeft, Home } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="min-h-screen bg-cream-50 flex flex-col justify-center items-center p-4">
      <Card className="max-w-md w-full p-8 text-center bg-white rounded-xl shadow-md">
        <div className="mb-6">
          <h1 className="text-6xl font-bold text-teal-800 mb-2">404</h1>
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">Page Not Found</h2>
          <p className="text-gray-600 mb-6">
            Sorry, we couldn't find the page you're looking for. 
            The page may have been moved or doesn't exist.
          </p>
        </div>
        
        <div className="flex flex-col gap-3">
          <Link href="/">
            <Button className="w-full bg-teal-600 hover:bg-teal-700 text-white">
              <Home className="h-4 w-4 mr-2" />
              Go Home
            </Button>
          </Link>
          
          <Link href="/chat">
            <Button variant="outline" className="w-full border-teal-600 text-teal-600 hover:bg-teal-50">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Chat
            </Button>
          </Link>
        </div>
      </Card>
    </div>
  )
} 