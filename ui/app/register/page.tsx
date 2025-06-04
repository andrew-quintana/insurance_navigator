"use client"

import React, { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ArrowLeft, Mail, Lock, User, Eye, EyeOff, Check } from "lucide-react"

interface RegisterResponse {
  access_token: string
  token_type: string
}

interface ValidationError {
  type: string
  loc: string[]
  msg: string
  input?: unknown
}

interface ErrorResponse {
  detail: string | ValidationError[]
}

export default function RegisterPage() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    confirmPassword: "",
    full_name: "",
  })
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

  // Check if passwords match and both have content
  const passwordsMatch = formData.password.length > 0 && 
                        formData.confirmPassword.length > 0 && 
                        formData.password === formData.confirmPassword

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    
    // Clear errors when user starts typing
    if (error) setError("")
    if (validationErrors[name]) {
      setValidationErrors(prev => ({ ...prev, [name]: "" }))
    }
  }

  const validateForm = () => {
    const errors: Record<string, string> = {}

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(formData.email)) {
      errors.email = "Please enter a valid email address"
    }

    // Full name validation
    if (formData.full_name.trim().length < 2) {
      errors.full_name = "Full name must be at least 2 characters"
    }

    // Password validation
    if (formData.password.length < 6) {
      errors.password = "Password must be at least 6 characters"
    }

    // Confirm password validation
    if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = "Passwords do not match"
    }

    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

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
    
    return "Registration failed. Please try again."
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError("")

    // Validate form
    if (!validateForm()) {
      setIsLoading(false)
      return
    }

    try {
      const response = await fetch("http://localhost:8000/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password,
          full_name: formData.full_name,
        }),
      })

      if (response.ok) {
        const data: RegisterResponse = await response.json()
        
        // Store the JWT token
        localStorage.setItem("token", data.access_token)
        localStorage.setItem("tokenType", data.token_type)
        
        // Redirect to welcome page for new users
        router.push("/welcome")
      } else {
        const errorData: ErrorResponse = await response.json()
        setError(formatApiError(errorData))
      }
    } catch (err) {
      console.error("Registration error:", err)
      setError("Network error. Please check your connection and try again.")
    } finally {
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
          <h1 className="text-xl font-semibold text-teal-800 mx-auto pr-8">Create Account</h1>
        </div>
      </header>

      {/* Registration Form */}
      <div className="flex-1 container mx-auto max-w-md p-4 flex flex-col justify-center">
        <Card className="p-8 bg-white rounded-xl shadow-md">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-teal-800 mb-2">Join Medicare Navigator</h2>
            <p className="text-gray-600">Create your account to get personalized help</p>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Full Name Field */}
            <div>
              <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 mb-2">
                Full Name
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  id="full_name"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleInputChange}
                  required
                  className={`w-full pl-10 pr-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent ${
                    validationErrors.full_name ? "border-red-300" : "border-gray-300"
                  }`}
                  placeholder="Enter your full name"
                />
              </div>
              {validationErrors.full_name && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.full_name}</p>
              )}
            </div>

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
                  className={`w-full pl-10 pr-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent ${
                    validationErrors.email ? "border-red-300" : "border-gray-300"
                  }`}
                  placeholder="Enter your email"
                />
              </div>
              {validationErrors.email && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.email}</p>
              )}
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
                  className={`w-full pl-10 pr-12 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent ${
                    validationErrors.password 
                      ? "border-red-300" 
                      : passwordsMatch 
                        ? "border-green-400 bg-green-50" 
                        : "border-gray-300"
                  }`}
                  placeholder="Create a password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className={`absolute right-3 top-1/2 transform -translate-y-1/2 h-5 w-5 hover:text-gray-600 transition-colors ${
                    passwordsMatch ? "text-green-600" : "text-gray-400"
                  }`}
                >
                  {passwordsMatch ? <Check /> : showPassword ? <EyeOff /> : <Eye />}
                </button>
              </div>
              {validationErrors.password && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.password}</p>
              )}
              {passwordsMatch && !validationErrors.password && (
                <p className="mt-1 text-sm text-green-600">Passwords match!</p>
              )}
            </div>

            {/* Confirm Password Field */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  id="confirmPassword"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  required
                  className={`w-full pl-10 pr-12 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent ${
                    validationErrors.confirmPassword 
                      ? "border-red-300" 
                      : passwordsMatch 
                        ? "border-green-400 bg-green-50" 
                        : "border-gray-300"
                  }`}
                  placeholder="Confirm your password"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className={`absolute right-3 top-1/2 transform -translate-y-1/2 h-5 w-5 hover:text-gray-600 transition-colors ${
                    passwordsMatch ? "text-green-600" : "text-gray-400"
                  }`}
                >
                  {passwordsMatch ? <Check /> : showConfirmPassword ? <EyeOff /> : <Eye />}
                </button>
              </div>
              {validationErrors.confirmPassword && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.confirmPassword}</p>
              )}
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={isLoading}
              className="w-full bg-teal-700 hover:bg-teal-800 text-white py-3 rounded-lg font-medium transition-colors"
            >
              {isLoading ? "Creating Account..." : "Create Account"}
            </Button>
          </form>

          {/* Login Link */}
          <div className="mt-6 text-center">
            <p className="text-gray-600">
              Already have an account?{" "}
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