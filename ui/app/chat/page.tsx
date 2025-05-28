"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { SendHorizontal, ArrowLeft, Upload, User } from "lucide-react"

type Message = {
  id: number
  sender: "bot" | "user"
  text: string
  options?: string[]
  metadata?: Record<string, unknown>
  workflow_type?: string
}

interface ChatResponse {
  text: string
  metadata: Record<string, unknown>
  conversation_id: string
  workflow_type: string
}

interface UserInfo {
  id: string
  email: string
  name: string
}

export default function ChatPage() {
  const router = useRouter()
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState("")
  const [conversationId, setConversationId] = useState<string>("")
  const [isLoading, setIsLoading] = useState(false)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isCheckingAuth, setIsCheckingAuth] = useState(true)
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null)
  const [authError, setAuthError] = useState("")
  const [sessionWarning, setSessionWarning] = useState("")
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const sessionCheckInterval = useRef<NodeJS.Timeout | null>(null)
  const lastActivityTime = useRef<number>(Date.now())
  const isCheckingAuthRef = useRef(false)

  // Check authentication on component mount
  useEffect(() => {
    checkAuthentication()
    
    // Set up session monitoring (OWASP recommendation)
    sessionCheckInterval.current = setInterval(() => {
      const now = Date.now()
      const timeSinceActivity = now - lastActivityTime.current
      
      // Check if session is approaching expiration (25 minutes = 1500000ms)
      if (timeSinceActivity > 1500000) {
        setSessionWarning("Your session will expire in 5 minutes due to inactivity.")
      }
      
      // Auto-logout after 30 minutes of inactivity (1800000ms)
      if (timeSinceActivity > 1800000) {
        logout()
      }
    }, 60000) // Check every minute
    
    return () => {
      if (sessionCheckInterval.current) {
        clearInterval(sessionCheckInterval.current)
      }
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-scroll to the bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Focus the input field when the component mounts
  useEffect(() => {
    if (isAuthenticated && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isAuthenticated])

  // Track user activity for session management
  const updateActivity = () => {
    lastActivityTime.current = Date.now()
    setSessionWarning("") // Clear any session warnings
  }

  const checkAuthentication = async () => {
    // Prevent multiple simultaneous authentication checks
    if (isCheckingAuthRef.current) {
      console.log("🔄 Auth check already in progress, skipping...")
      return
    }
    
    isCheckingAuthRef.current = true
    setIsCheckingAuth(true) // Show loading state
    let shouldRetry = false
    
    try {
      const token = localStorage.getItem("token")
      const tokenType = localStorage.getItem("tokenType")

      console.log("🔐 Chat: Checking authentication...")
      console.log("🎫 Token exists:", !!token)

      if (!token) {
        console.log("❌ No token found, redirecting to login")
        router.push("/login")
        return
      }

      console.log("🚀 Validating token with backend...")
      const response = await fetch("http://localhost:8000/me", {
        headers: {
          "Authorization": `${tokenType || "Bearer"} ${token}`,
        },
      })

      console.log("📡 Auth response status:", response.status)

      if (response.ok) {
        const userData: UserInfo = await response.json()
        console.log("✅ Authentication successful, user:", userData.name)
        setUserInfo(userData)
        setIsAuthenticated(true)
        setAuthError("") // Clear any previous errors
        
        // Add initial bot message only if no messages exist
        if (messages.length === 0) {
          const initialMessage: Message = {
            id: 1,
            sender: "bot",
            text: `Hello ${userData.name}! I'm your Medicare Navigator. I can help you with Medicare questions, find healthcare providers, understand your benefits, and more. What would you like to know today?`,
          }
          setMessages([initialMessage])
        }
      } else {
        console.log("❌ Auth failed with status:", response.status)
        // Handle specific error cases
        if (response.status === 401) {
          // Token expired or invalid - clear and redirect
          console.log("🗑️ Clearing invalid token")
          localStorage.removeItem("token")
          localStorage.removeItem("tokenType")
          router.push("/login")
        } else if (response.status >= 500) {
          // Server error - show error but don't clear session yet
          console.log("🔥 Server error, retrying...")
          setAuthError("Server temporarily unavailable. Please try again in a moment.")
        } else {
          // Other errors - clear session
          console.log("🗑️ Clearing session due to auth error")
          setAuthError("Authentication failed. Please log in again.")
          localStorage.removeItem("token")
          localStorage.removeItem("tokenType")
          router.push("/login")
        }
      }
    } catch (err) {
      console.error("🔥 Auth check network error:", err)
      
      // Better error handling for specific error types
      if (err instanceof TypeError && err.message.includes("fetch")) {
        setAuthError("Unable to connect to server. Retrying in 3 seconds...")
        shouldRetry = true
        // Retry after 3 seconds
        setTimeout(() => {
          console.log("🔄 Retrying authentication...")
          isCheckingAuthRef.current = false // Reset flag before retry
          checkAuthentication()
        }, 3000)
      } else {
        // Network error - don't immediately clear session, allow retry
        setAuthError("Network error. Checking connection... Please wait.")
        shouldRetry = true
        
        // Retry after 2 seconds
        setTimeout(() => {
          console.log("🔄 Retrying authentication...")
          isCheckingAuthRef.current = false // Reset flag before retry
          checkAuthentication()
        }, 2000)
      }
    } finally {
      // Only reset the flag and loading state if we're not retrying
      if (!shouldRetry) {
        isCheckingAuthRef.current = false
        setIsCheckingAuth(false)
      }
    }
  }

  const logout = () => {
    localStorage.removeItem("token")
    localStorage.removeItem("tokenType")
    router.push("/")
  }

  const sendMessage = async (messageText: string) => {
    if (!messageText.trim() || isLoading) return

    // Track user activity
    updateActivity()

    // Add user message
    const userMessage: Message = {
      id: messages.length + 1,
      sender: "user",
      text: messageText,
    }

    setMessages(prevMessages => [...prevMessages, userMessage])
    setIsLoading(true)

    try {
      const token = localStorage.getItem("token")
      const tokenType = localStorage.getItem("tokenType")

      // Validate session before sending message
      if (!token) {
        router.push("/login")
        return
      }

      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `${tokenType || "Bearer"} ${token}`,
        },
        body: JSON.stringify({
          message: messageText,
          conversation_id: conversationId,
        }),
      })

      if (response.ok) {
        const data: ChatResponse = await response.json()
        
        // Update conversation ID if this is the first message
        if (!conversationId) {
          setConversationId(data.conversation_id)
        }

        // Add bot response
        const botMessage: Message = {
          id: messages.length + 2,
          sender: "bot",
          text: data.text,
          metadata: data.metadata,
          workflow_type: data.workflow_type,
        }

        setMessages(prevMessages => [...prevMessages, botMessage])
      } else {
        if (response.status === 401) {
          setAuthError("Your session has expired. Please log in again.")
          logout()
          return
        }

        // Handle error response
        const errorMessage: Message = {
          id: messages.length + 2,
          sender: "bot",
          text: "I apologize, but I'm experiencing some technical difficulties. Please try rephrasing your question or contact support if the issue persists.",
        }
        setMessages(prevMessages => [...prevMessages, errorMessage])
      }
    } catch (err) {
      console.error("Chat error:", err)
      const errorMessage: Message = {
        id: messages.length + 2,
        sender: "bot",
        text: "I'm having trouble connecting right now. Please check your internet connection and try again.",
      }
      setMessages(prevMessages => [...prevMessages, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSendMessage = () => {
    const message = inputValue.trim()
    if (message) {
      updateActivity() // Track activity
      sendMessage(message)
      setInputValue("")
    }
  }

  const handleOptionClick = (option: string) => {
    updateActivity() // Track activity
    sendMessage(option)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
    // Track any key activity
    updateActivity()
  }

  const handleFileUpload = async () => {
    try {
      const token = localStorage.getItem("token")
      const tokenType = localStorage.getItem("tokenType")

      const response = await fetch("http://localhost:8000/upload-policy", {
        method: "POST",
        headers: {
          "Authorization": `${tokenType || "Bearer"} ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        const uploadMessage: Message = {
          id: messages.length + 1,
          sender: "bot",
          text: data.message,
        }
        setMessages(prevMessages => [...prevMessages, uploadMessage])
      }
    } catch (err) {
      console.error("Upload error:", err)
    }
  }

  // Show loading screen while checking authentication
  if (isCheckingAuth) {
    return (
      <div className="min-h-screen bg-cream-50 flex items-center justify-center">
        <Card className="p-8 bg-white rounded-xl shadow-md max-w-md">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-teal-800 mb-4">Loading Medicare Navigator...</h2>
            {authError && (
              <p className="text-red-600 mb-4">{authError}</p>
            )}
            {sessionWarning && (
              <p className="text-orange-600 mb-4">{sessionWarning}</p>
            )}
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-700 mx-auto"></div>
            <p className="text-gray-600 mt-4 text-sm">Verifying your session...</p>
          </div>
        </Card>
      </div>
    )
  }

  // Show error screen if authentication failed but not checking
  if (!isAuthenticated && !isCheckingAuth) {
    return (
      <div className="min-h-screen bg-cream-50 flex items-center justify-center">
        <Card className="p-8 bg-white rounded-xl shadow-md max-w-md">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-teal-800 mb-4">Authentication Required</h2>
            {authError && (
              <p className="text-red-600 mb-4">{authError}</p>
            )}
            <p className="text-gray-600 mb-4">Please log in to access the Medicare Navigator.</p>
            <Button 
              onClick={() => router.push("/login")}
              className="bg-teal-700 hover:bg-teal-800 text-white"
            >
              Go to Login
            </Button>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-cream-50 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm p-4">
        <div className="container mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center text-teal-700 hover:text-teal-800 transition-colors">
            <ArrowLeft className="h-5 w-5 mr-2" />
            <span>Return to Home</span>
          </Link>
          <h1 className="text-xl font-semibold text-teal-800">Medicare Navigator Chat</h1>
          <div className="flex items-center space-x-4">
            <div className="flex items-center text-teal-700">
              <User className="h-5 w-5 mr-2" />
              <span className="text-sm">{userInfo?.name}</span>
            </div>
            <Button
              onClick={logout}
              variant="outline"
              className="text-teal-700 border-teal-300 hover:bg-teal-50"
            >
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Chat Container */}
      <div className="flex-1 container mx-auto max-w-4xl p-4 flex flex-col">
        <Card className="flex-1 flex flex-col overflow-hidden bg-white rounded-xl shadow-md mb-4">
          {/* Messages Area */}
          <div className="flex-1 p-4 overflow-y-auto">
            <div className="space-y-4">
              {messages.map((message) => (
                <div key={message.id} className={`flex ${message.sender === "bot" ? "justify-start" : "justify-end"}`}>
                  <div
                    className={`max-w-3/4 rounded-xl p-4 ${
                      message.sender === "bot" ? "bg-teal-100 text-teal-800" : "bg-sky-100 text-sky-800"
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{message.text}</p>
                    
                    {message.options && (
                      <div className="mt-4 flex flex-wrap gap-2">
                        {message.options.map((option, index) => (
                          <Button
                            key={index}
                            variant="outline"
                            className="bg-white text-teal-700 border-teal-300 hover:bg-teal-50 hover:text-teal-800 mt-1"
                            onClick={() => handleOptionClick(option)}
                            disabled={isLoading}
                          >
                            {option}
                          </Button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              
              {/* Loading indicator */}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-teal-100 text-teal-800 rounded-xl p-4">
                    <div className="flex items-center space-x-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-teal-700"></div>
                      <span>Thinking...</span>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input Area */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center space-x-2">
              <Button
                onClick={handleFileUpload}
                variant="outline"
                className="text-teal-700 border-teal-300 hover:bg-teal-50 p-3"
                disabled={isLoading}
                title="Upload Policy Document"
              >
                <Upload className="h-5 w-5" />
              </Button>
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your Medicare question here..."
                disabled={isLoading}
                className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 disabled:bg-gray-100"
              />
              <Button
                onClick={handleSendMessage}
                disabled={isLoading || !inputValue.trim()}
                className="bg-teal-700 hover:bg-teal-800 text-white p-3 h-[46px]"
              >
                <SendHorizontal className="h-5 w-5" />
              </Button>
            </div>
          </div>
        </Card>

        {/* Info Card */}
        <Card className="p-4 bg-sky-50 text-teal-800 text-sm rounded-xl">
          <p className="font-medium">Privacy & Security</p>
          <p className="mt-1">
            Your Medicare information is kept secure and private. All conversations are encrypted and we follow 
            HIPAA compliance standards to protect your health information.
          </p>
        </Card>
      </div>
    </div>
  )
}
