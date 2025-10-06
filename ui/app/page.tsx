"use client"

import React, { useState, useEffect } from "react"
import Link from "next/link"
import Image from "next/image"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { useAuth } from "@/components/auth/SessionManager"
import {
  CheckCircle,
  ChevronRight,
  MessageSquare,
  FileText,
  PlayCircle,
  Upload,
  Calendar,
  DollarSign,
  Activity,
  LogIn,
} from "lucide-react"

export default function Home() {
  const router = useRouter()
  const { user, loading } = useAuth()
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Set loading state based on auth loading
    setIsLoading(loading)
  }, [loading])

  const handleStartNow = () => {
    if (user) {
      router.push("/chat")
    } else {
      router.push("/register")
    }
  }

  const handleLogout = async () => {
    // This will be handled by the AuthProvider's signOut method
    // The user will be automatically redirected when the auth state changes
  }

  return (
    <div className="min-h-screen bg-cream-50">
      {/* Navigation */}
      <nav className="container mx-auto py-4 px-4 flex justify-between items-center">
        <div className="font-semibold text-xl text-teal-700">
          <span className="text-terracotta">Insurance</span> Navigator
        </div>
        <div className="flex items-center space-x-3">
          {isLoading ? (
            // Loading placeholder - prevent flash
            <div className="flex items-center space-x-3">
              <div className="w-20 h-10 bg-gray-200 animate-pulse rounded"></div>
              <div className="w-24 h-10 bg-gray-200 animate-pulse rounded"></div>
            </div>
          ) : user ? (
            // Authenticated user menu
            <>
              <div className="flex items-center space-x-4">
                <div className="flex items-center text-teal-700">
                  <span className="text-sm font-medium">Welcome, {user.user_metadata?.full_name || user.email}</span>
                </div>
                <Button
                  variant="outline"
                  className="text-teal-700 border-teal-700 hover:bg-teal-50"
                  onClick={() => router.push("/chat")}
                >
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Chat
                </Button>
                <Button
                  variant="outline"
                  className="text-gray-600 border-gray-300 hover:bg-gray-50"
                  onClick={handleLogout}
                >
                  Sign Out
                </Button>
              </div>
            </>
          ) : (
            // Unauthenticated user buttons
            <>
              <Link href="/login">
                <Button variant="outline" className="text-teal-700 border-teal-700 hover:bg-teal-50">
                  <LogIn className="h-4 w-4 mr-2" />
                  Sign In
                </Button>
              </Link>
              <Link href="/register">
                <Button className="bg-teal-700 hover:bg-teal-800 text-white">
                  Get Started
                </Button>
              </Link>
            </>
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <section className="py-16 md:py-24 relative">
        {/* Full-width watercolor background */}
        <div className="absolute inset-0 bg-gradient-to-br from-cream-100 to-sky-50">
          <div className="h-full w-full overflow-hidden">
            <Image
              src="/images/interface_banner.png"
              alt="Watercolor illustration of a medical facility in a serene landscape"
              fill
              className="object-cover object-center opacity-90"
              priority
              onError={(e) => {
                // Hide image on error, fallback to gradient background
                e.currentTarget.style.display = 'none'
              }}
            />
          </div>
        </div>

        {/* Content positioned with z-index to appear above the background */}
        <div className="container mx-auto px-4 relative z-10">
          <div className="max-w-3xl bg-white/80 backdrop-blur-sm p-8 rounded-2xl shadow-sm">
            <h1 className="text-4xl md:text-5xl font-bold text-teal-800 mb-6">Navigate Insurance with Confidence</h1>
            <p className="text-xl text-teal-700 mb-8">
              Get personalized questions to ask your doctor, understand your insurance plan, and feel more in control —
              all in one secure place.
            </p>
            <Button
              onClick={handleStartNow}
              size="lg"
              className="bg-terracotta hover:bg-terracotta-600 text-white px-8 py-6 text-lg rounded-xl shadow-lg transition-all"
              disabled={isLoading}
            >
              {isLoading ? "Loading..." : user ? "Continue to Chat" : "Get Started"}
              <ChevronRight className="ml-2 h-5 w-5" />
            </Button>
          </div>
        </div>
      </section>

      {/* Sample Output + How It Works */}
      <section className="container mx-auto px-4 py-16 bg-white rounded-t-3xl shadow-sm">
        <div className="grid md:grid-cols-2 gap-8 items-start">
          {/* Sample Output */}
          <div>
            <h2 className="text-3xl font-bold text-teal-800 mb-8">Demo Setup</h2>
            <Card className="p-6 shadow-lg rounded-xl bg-white">
              <div className="mb-6 p-4 bg-sky-50 rounded-lg">
                <p className="text-teal-800 font-medium mb-4">
                  Try the Insurance Navigator with a pre-loaded sample policy document.
                </p>
                <p className="text-teal-700">
                  <span className="font-medium">View Sample Policy Document:</span>{" "}
                  <a 
                    href="https://github.com/andrew-quintana/insurance_navigator/blob/7970075fb90ba8c6e7215ed6668b0dd40dfb06e1/examples/scan_classic_hmo.pdf"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 underline"
                  >
                    a pre-uploaded 250-page Medicare policy document
                  </a>
                </p>
              </div>
              <div className="space-y-4">
                <div className="border-l-4 border-teal-500 pl-4">
                  <h3 className="font-semibold text-teal-800 mb-2">What you can test:</h3>
                  <ul className="space-y-2">
                    {["Ask questions about coverage", "Understand copays and deductibles", "Find mental health services", "Get personalized guidance"].map(
                      (item, i) => (
                        <li key={i} className="flex items-start">
                          <CheckCircle className="h-5 w-5 text-teal-500 mr-2 flex-shrink-0 mt-0.5" />
                          <span className="text-teal-700">{item}</span>
                        </li>
                      ),
                    )}
                  </ul>
                </div>
                <p className="text-teal-700 italic mt-4 p-3 bg-cream-50 rounded-lg">
                  This demo uses a real insurance policy document to show how the Insurance Navigator can help you understand your coverage.
                </p>
              </div>
            </Card>
          </div>

          {/* How It Works + Video */}
          <div>
            <h2 className="text-3xl font-bold text-teal-800 mb-8">How It Works</h2>
            <div className="space-y-6 mb-8">
              <div className="flex items-start p-4 bg-cream-50 rounded-xl">
                <div className="bg-cream-100 w-12 h-12 rounded-full flex items-center justify-center mr-4 flex-shrink-0">
                  <Upload className="h-6 w-6 text-teal-700" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-teal-800 mb-1">Step 1</h3>
                  <p className="text-teal-700">Upload your insurance plan or start with a question</p>
                </div>
              </div>

              <div className="flex items-start p-4 bg-sky-50 rounded-xl">
                <div className="bg-sky-100 w-12 h-12 rounded-full flex items-center justify-center mr-4 flex-shrink-0">
                  <MessageSquare className="h-6 w-6 text-sky-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-teal-800 mb-1">Step 2</h3>
                  <p className="text-teal-700">Chat securely with our Insurance Navigator</p>
                </div>
              </div>

              <div className="flex items-start p-4 bg-teal-50 rounded-xl">
                <div className="bg-teal-100 w-12 h-12 rounded-full flex items-center justify-center mr-4 flex-shrink-0">
                  <FileText className="h-6 w-6 text-teal-700" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-teal-800 mb-1">Step 3</h3>
                  <p className="text-teal-700">Keep track of insights anytime</p>
                </div>
              </div>
            </div>

            {/* Video directly under How It Works */}
            <div className="aspect-w-16 aspect-h-9 bg-sky-50 rounded-xl overflow-hidden relative border border-sky-200">
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <PlayCircle className="h-20 w-20 text-teal-700 opacity-80 mb-4" />
                <p className="text-teal-800 font-medium">Demo Video</p>
                <p className="text-teal-600 text-sm">Coming Soon</p>
              </div>
            </div>
            <p className="text-center text-teal-700 mt-4">See how Insurance Navigator helps you stay one step ahead.</p>
          </div>
        </div>
      </section>


    </div>
  )
}
