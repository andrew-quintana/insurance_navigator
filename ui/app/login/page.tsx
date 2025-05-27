"use client"

import React, { useState, useEffect } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ArrowLeft, Mail, Lock, Eye, EyeOff } from "lucide-react"

interface LoginResponse {
  access_token: string
  token_type: string
}

interface ValidationError {
  type: string
  loc: string[]
  msg: string
  input?: any
}

interface ErrorResponse {
  detail: string | ValidationError[]
}

export default function LoginPage() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  })
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking")

  // Check backend status on component mount
  useEffect(() => {
    const checkBackendStatus = async () => {
      try {
        console.log("🏥 Checking backend health...")
        const response = await fetch("http://localhost:8000/health", {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        })
        
        if (response.ok) {
          console.log("✅ Backend is online")
          setBackendStatus("online")
        } else {
          console.log("⚠️ Backend responded but not healthy")
          setBackendStatus("offline")
        }
      } catch (err) {
        console.log("❌ Backend is offline:", err)
        setBackendStatus("offline")
      }
    }

    checkBackendStatus()
  }, [])

  // Helper function to format API errors
  const formatApiError = (errorData: ErrorResponse): string => {
    if (typeof errorData.detail === "string") {
      return errorData.detail
    }
    
    if (Array.isArray(errorData.detail)) {
      // Handle FastAPI validation errors
      const messages = errorData.detail.map((err: ValidationError) => {
        const field = err.loc.join(" → ")
        return `${field}: ${err.msg}`
      })
      return messages.join(", ")
    }
    
    return "Login failed. Please try again."
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    // Clear error when user starts typing
    if (error) setError("")
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError("")

    console.log("🔐 Login attempt started")
    console.log("📧 Email:", formData.email)
    console.log("🌐 Backend URL:", "http://localhost:8000/login")

    try {
      console.log("🚀 Sending login request...")
      const response = await fetch("http://localhost:8000/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      })

      console.log("📡 Response status:", response.status)
      console.log("📡 Response ok:", response.ok)

      if (response.ok) {
        const data: LoginResponse = await response.json()
        console.log("✅ Login successful, token received")
        
        // Store the JWT token securely
        localStorage.setItem("token", data.access_token)
        localStorage.setItem("tokenType", data.token_type)
        
        console.log("🚀 Redirecting to chat...")
        // Redirect to chat page for returning users
        router.push("/chat")
      } else {
        console.log("❌ Login failed with status:", response.status)
        try {
          const errorData: ErrorResponse = await response.json()
          console.log("📄 Error response:", errorData)
          setError(formatApiError(errorData))
        } catch (parseError) {
          console.log("⚠️ Could not parse error response:", parseError)
          setError(`Login failed with status ${response.status}. Please try again.`)
        }
        
        // Clear any existing invalid tokens
        localStorage.removeItem("token")
        localStorage.removeItem("tokenType")
      }
    } catch (err) {
      console.error("🔥 Network/Connection error:", err)
      
      // Determine error type for better user feedback
      if (err instanceof TypeError && err.message.includes("fetch")) {
        setError("Unable to connect to server. Please check if the backend is running and try again.")
      } else if (err instanceof Error) {
        setError(`Connection error: ${err.message}. Please check your network connection.`)
      } else {
        setError("Network error. Please check your connection and try again.")
      }
      
      // Clear any existing tokens on network error
      localStorage.removeItem("token")
      localStorage.removeItem("tokenType")
    } finally {
      console.log("🏁 Login attempt completed")
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-cream-50 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm p-4">
        <div className="container mx-auto flex items-center">
          <Link href="/" className="flex items-center text-teal-700 hover:text-teal-800 transition-colors">
            <ArrowLeft className="h-5 w-5 mr-2" />
            <span>Return to Home</span>
          </Link>
          <h1 className="text-xl font-semibold text-teal-800 mx-auto pr-8">Sign In</h1>
        </div>
      </header>

      {/* Login Form */}
      <div className="flex-1 container mx-auto max-w-md p-4 flex flex-col justify-center">
        <Card className="p-8 bg-white rounded-xl shadow-md">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-teal-800 mb-2">Welcome Back</h2>
            <p className="text-gray-600">Sign in to your Medicare Navigator account</p>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          {backendStatus === "offline" && (
            <div className="mb-6 p-4 bg-orange-50 border border-orange-200 rounded-lg">
              <p className="text-orange-800 text-sm font-medium">⚠️ Server Connection Issue</p>
              <p className="text-orange-700 text-sm mt-1">
                Unable to connect to the backend server. Please ensure the server is running on port 8000.
              </p>
            </div>
          )}

          {backendStatus === "checking" && (
            <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-blue-800 text-sm">🔍 Checking server connection...</p>
            </div>
          )}

          {backendStatus === "online" && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-800 text-sm">✅ Server connection healthy</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  required
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                  placeholder="Enter your email"
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type={showPassword ? "text" : "password"}
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  required
                  className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff /> : <Eye />}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={isLoading}
              className="w-full bg-teal-700 hover:bg-teal-800 text-white py-3 rounded-lg font-medium transition-colors"
            >
              {isLoading ? "Signing In..." : "Sign In"}
            </Button>
          </form>

          {/* Forgot Password Link */}
          <div className="mt-4 text-center">
            <Link href="/forgot-password" className="text-teal-700 hover:text-teal-800 text-sm font-medium">
              Forgot your password?
            </Link>
          </div>

          {/* Register Link */}
          <div className="mt-6 text-center">
            <p className="text-gray-600">
              Don&rsquo;t have an account?{" "}
              <Link href="/register" className="text-teal-700 hover:text-teal-800 font-medium">
                Sign up here
              </Link>
            </p>
          </div>
        </Card>
      </div>
    </div>
  )
} 