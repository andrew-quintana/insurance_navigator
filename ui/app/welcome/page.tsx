"use client"

import React, { useEffect, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ArrowLeft, PlayCircle, ChevronRight, CheckCircle, User, ArrowRight } from "lucide-react"

interface UserInfo {
  id: string
  email: string
  name: string
}

export default function WelcomePage() {
  const router = useRouter()
  const [user, setUser] = useState<UserInfo | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem("token")
      if (!token) {
        router.push("/login")
        return
      }

      // Get API URL from environment variables (Vercel best practice)
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
      const authMeUrl = `${apiBaseUrl}/api/v1/auth/me`
      
      console.log("🌐 API Base URL:", apiBaseUrl)
      console.log("🔗 Auth Me URL:", authMeUrl)

      try {
        const response = await fetch(authMeUrl, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Accept': 'application/json',
          },
        })
        
        if (response.ok) {
          const userData: UserInfo = await response.json()
          setUser(userData)
        } else {
          // Token is invalid, redirect to login
          localStorage.removeItem("token")
          localStorage.removeItem("tokenType")
          router.push("/login")
        }
      } catch (error) {
        console.error("Auth check failed:", error)
        localStorage.removeItem("token")
        localStorage.removeItem("tokenType")
        router.push("/login")
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()
  }, [router])

  const handleNext = () => {
    if (user) {
      router.push("/chat")
    } else {
      router.push("/login")
    }
  }

  return (
    <div className="min-h-screen bg-cream-50">
      {/* Header */}
      <header className="bg-white shadow-sm p-4">
        <div className="container mx-auto flex items-center">
          <Link href="/" className="flex items-center text-teal-700 hover:text-teal-800 transition-colors">
            <ArrowLeft className="h-5 w-5 mr-2" />
            <span>Back to Home</span>
          </Link>
          <h1 className="text-xl font-semibold text-teal-800 mx-auto pr-8">Welcome Guide</h1>
        </div>
      </header>

      {/* Welcome Content */}
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Welcome Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-teal-800 mb-4">
            Welcome to Medicare Navigator!
          </h1>
          <p className="text-xl text-teal-700 max-w-2xl mx-auto leading-relaxed">
            Your personal AI assistant for navigating Medicare plans, understanding benefits, and making informed healthcare decisions.
          </p>
        </div>

        {/* Demo Video Section */}
        <Card className="mb-12 p-8 bg-white rounded-xl shadow-md">
          <h2 className="text-2xl font-bold text-teal-800 mb-6 text-center">
            See How It Works
          </h2>
          
          {/* Video Placeholder - Same as homepage */}
          <div className="aspect-w-16 aspect-h-9 bg-sky-50 rounded-xl overflow-hidden relative border border-sky-200 mb-6">
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <PlayCircle className="h-20 w-20 text-teal-700 opacity-80 mb-4" />
              <p className="text-teal-800 font-medium">Demo Video</p>
              <p className="text-teal-600 text-sm">Coming Soon</p>
            </div>
          </div>
          
          <p className="text-center text-teal-700 text-lg">
            Watch how Medicare Navigator helps you stay one step ahead with personalized guidance.
          </p>
        </Card>

        {/* What You Can Do Section */}
        <Card className="mb-12 p-8 bg-white rounded-xl shadow-md">
          <h2 className="text-2xl font-bold text-teal-800 mb-8 text-center">
            What You Can Do
          </h2>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div className="flex items-start space-x-4">
              <div className="bg-teal-100 p-3 rounded-full flex-shrink-0">
                <CheckCircle className="h-6 w-6 text-teal-700" />
              </div>
              <div>
                <h3 className="font-semibold text-teal-800 mb-2">Compare Medicare Plans</h3>
                <p className="text-gray-600">Get personalized recommendations based on your health needs, budget, and preferred doctors.</p>
              </div>
            </div>
            
            <div className="flex items-start space-x-4">
              <div className="bg-sky-100 p-3 rounded-full flex-shrink-0">
                <CheckCircle className="h-6 w-6 text-sky-700" />
              </div>
              <div>
                <h3 className="font-semibold text-teal-800 mb-2">Understand Your Benefits</h3>
                <p className="text-gray-600">Decode complex Medicare terminology and understand exactly what&rsquo;s covered.</p>
              </div>
            </div>
            
            <div className="flex items-start space-x-4">
              <div className="bg-terracotta-100 p-3 rounded-full flex-shrink-0">
                <CheckCircle className="h-6 w-6 text-terracotta-700" />
              </div>
              <div>
                <h3 className="font-semibold text-teal-800 mb-2">Track Important Dates</h3>
                <p className="text-gray-600">Never miss enrollment periods, renewals, or important Medicare deadlines.</p>
              </div>
            </div>
            
            <div className="flex items-start space-x-4">
              <div className="bg-cream-200 p-3 rounded-full flex-shrink-0">
                <CheckCircle className="h-6 w-6 text-teal-700" />
              </div>
              <div>
                <h3 className="font-semibold text-teal-800 mb-2">Get Instant Answers</h3>
                <p className="text-gray-600">Ask questions anytime and get immediate, accurate responses about Medicare.</p>
              </div>
            </div>
          </div>
        </Card>

        {/* How to Get Started */}
        <Card className="mb-12 p-8 bg-gradient-to-br from-teal-50 to-sky-50 rounded-xl shadow-md">
          <h2 className="text-2xl font-bold text-teal-800 mb-6 text-center">
            How to Get Started
          </h2>
          
          <div className="space-y-6">
            <div className="flex items-center space-x-4">
              <div className="bg-teal-700 text-white w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm">
                1
              </div>
              <p className="text-lg text-teal-800">
                <span className="font-semibold">Start a conversation</span> - Simply type your Medicare question or concern
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="bg-sky-700 text-white w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm">
                2
              </div>
              <p className="text-lg text-teal-800">
                <span className="font-semibold">Get personalized guidance</span> - Receive tailored advice based on your specific situation
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="bg-terracotta-700 text-white w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm">
                3
              </div>
              <p className="text-lg text-teal-800">
                <span className="font-semibold">Take action</span> - Follow clear, step-by-step recommendations to optimize your Medicare experience
              </p>
            </div>
          </div>
        </Card>

        {/* Call to Action */}
        <div className="text-center">
          <Button 
            onClick={handleNext}
            disabled={isLoading}
            className="bg-teal-700 hover:bg-teal-800 text-white px-8 py-4 text-lg font-semibold rounded-lg transition-colors shadow-md hover:shadow-lg disabled:opacity-50"
          >
            {isLoading 
              ? "Loading..." 
              : user 
                ? "Start Chat" 
                : "Sign In"
            }
            <ChevronRight className="ml-2 h-5 w-5" />
          </Button>
          
          <p className="mt-4 text-gray-600">
            {isLoading
              ? "Verifying your session..."
              : user 
                ? "You're all set! Click to start your Medicare conversation."
                : "Please sign in to begin your Medicare journey."
            }
          </p>
        </div>
      </div>
    </div>
  )
} 