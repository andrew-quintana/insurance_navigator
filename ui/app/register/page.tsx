"use client"

import React, { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ArrowLeft, Mail, Lock, User, Eye, EyeOff, Check } from "lucide-react"
import RegisterForm from "@/components/auth/RegisterForm"

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

  const handleRegisterSuccess = () => {
    router.push("/welcome")
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
        <RegisterForm onSuccess={handleRegisterSuccess} />
      </div>
    </div>
  )
} 