"use client"

import React, { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ArrowLeft, Mail, CheckCircle } from "lucide-react"

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitted, setIsSubmitted] = useState(false)
  const [error, setError] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError("")

    // Get API URL from environment variables (Vercel best practice)
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
    const forgotPasswordUrl = `${apiBaseUrl}/api/v1/auth/forgot-password`
    
    console.log("🌐 API Base URL:", apiBaseUrl)
    console.log("🔗 Forgot Password URL:", forgotPasswordUrl)

    try {
      const response = await fetch(forgotPasswordUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({ email }),
      })
      
      if (response.ok) {
        setIsSubmitted(true)
      } else {
        console.log("❌ Forgot password failed with status:", response.status)
        setError("Failed to send reset email. Please try again.")
      }
    } catch (err) {
      console.error("Password reset error:", err)
      if (err instanceof Error) {
        setError(`Connection error: ${err.message}. Please check your network connection.`)
      } else {
        setError("Network error. Please check your connection and try again.")
      }
    } finally {
      setIsLoading(false)
    }
  }

  if (isSubmitted) {
    return (
      <div className="min-h-screen bg-cream-50 flex flex-col">
        {/* Header */}
        <header className="bg-white shadow-sm p-4">
          <div className="container mx-auto flex items-center">
            <Link href="/login" className="flex items-center text-teal-700 hover:text-teal-800 transition-colors">
              <ArrowLeft className="h-5 w-5 mr-2" />
              <span>Back to Sign In</span>
            </Link>
            <h1 className="text-xl font-semibold text-teal-800 mx-auto pr-8">Password Reset</h1>
          </div>
        </header>

        {/* Success Message */}
        <div className="flex-1 container mx-auto max-w-md p-4 flex flex-col justify-center">
          <Card className="p-8 bg-white rounded-xl shadow-md text-center">
            <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
            
            <h2 className="text-2xl font-bold text-teal-800 mb-4">Check Your Email</h2>
            
            <p className="text-gray-600 mb-6">
              We&rsquo;ve sent a password reset link to{" "}
              <span className="font-medium text-teal-700">{email}</span>
            </p>
            
            <p className="text-sm text-gray-500 mb-8">
              If you don&rsquo;t see the email in your inbox, please check your spam folder. 
              The link will expire in 24 hours.
            </p>

            <div className="space-y-3">
              <Link href="/login">
                <Button className="w-full bg-teal-700 hover:bg-teal-800 text-white py-3 rounded-lg font-medium transition-colors">
                  Back to Sign In
                </Button>
              </Link>
              
              <button
                onClick={() => {
                  setIsSubmitted(false)
                  setEmail("")
                }}
                className="w-full text-teal-700 hover:text-teal-800 py-2 text-sm font-medium transition-colors"
              >
                Send another email
              </button>
            </div>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-cream-50 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm p-4">
        <div className="container mx-auto flex items-center">
          <Link href="/login" className="flex items-center text-teal-700 hover:text-teal-800 transition-colors">
            <ArrowLeft className="h-5 w-5 mr-2" />
            <span>Back to Sign In</span>
          </Link>
          <h1 className="text-xl font-semibold text-teal-800 mx-auto pr-8">Reset Password</h1>
        </div>
      </header>

      {/* Reset Form */}
      <div className="flex-1 container mx-auto max-w-md p-4 flex flex-col justify-center">
        <Card className="p-8 bg-white rounded-xl shadow-md">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-teal-800 mb-2">Forgot Your Password?</h2>
            <p className="text-gray-600">
              No worries! Enter your email address and we&rsquo;ll send you a link to reset your password.
            </p>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 text-sm">{error}</p>
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
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value)
                    if (error) setError("")
                  }}
                  required
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                  placeholder="Enter your email address"
                />
              </div>
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={isLoading}
              className="w-full bg-teal-700 hover:bg-teal-800 text-white py-3 rounded-lg font-medium transition-colors"
            >
              {isLoading ? "Sending..." : "Send Reset Link"}
            </Button>
          </form>

          {/* Back to Login */}
          <div className="mt-6 text-center">
            <p className="text-gray-600">
              Remember your password?{" "}
              <Link href="/login" className="text-teal-700 hover:text-teal-800 font-medium">
                Sign in here
              </Link>
            </p>
          </div>
        </Card>
      </div>
    </div>
  )
} 