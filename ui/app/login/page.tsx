"use client"

import React from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { ArrowLeft } from "lucide-react"
import LoginForm from "@/components/auth/LoginForm"

export default function LoginPage() {
  const router = useRouter()

  const handleLoginSuccess = () => {
    router.push("/chat")
  }

  return (
    <div className="flex-1 bg-cream-50 flex flex-col">
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
        <LoginForm onSuccess={handleLoginSuccess} />
      </div>
    </div>
  )
} 