"use client"

import React, { useState, useEffect, useRef } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { SendHorizontal, ArrowLeft, Upload, User, Bot, LogOut, X, FileText, CheckCircle, AlertCircle } from "lucide-react"
import { api } from "@/lib/api-client"

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
    const checkAuth = async () => {
      const token = localStorage.getItem("token")
      if (!token) {
        router.push("/login")
        return
      }

      try {
        const response = await api.get('/auth/me')
        
        if (response.success && response.data) {
          setUserInfo(response.data as UserInfo)
          setIsAuthenticated(true)
          setAuthError("")
          
          // Add initial bot message only if no messages exist
          if (messages.length === 0) {
            const userName = (response.data as UserInfo).name || 'there'
            const initialMessage: Message = {
              id: 1,
              sender: "bot",
              text: `Hello ${userName}! I'm your Medicare Navigator. I can help you with Medicare questions, find healthcare providers, understand your benefits, and more. What would you like to know today?`,
            }
            setMessages([initialMessage])
          }
          setIsLoading(false)
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
      }
    }

    checkAuth()
    
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
  }, [router])

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

  const logout = () => {
    localStorage.removeItem("token")
    localStorage.removeItem("tokenType")
    router.push("/")
  }

  const sendMessage = async (messageText: string) => {
    if (!messageText.trim()) return

    const userMessage: Message = {
      id: messages.length + 1,
      text: messageText,
      sender: "user",
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    try {
      const response = await api.post<{ response: string }>('/chat/message', {
        message: messageText,
        conversation_id: conversationId,
      })

      if (response.success && response.data) {
        const botMessage: Message = {
          id: messages.length + 2,
          text: response.data.response,
          sender: "bot",
        }
        setMessages(prev => [...prev, botMessage])
      } else {
        throw new Error(response.error?.message || "Failed to get response")
      }
    } catch (error) {
      console.error("Chat error:", error)
      const errorMessage: Message = {
        id: messages.length + 2,
        text: "I'm sorry, I'm having trouble connecting right now. Please try again in a moment.",
        sender: "bot",
      }
      setMessages(prev => [...prev, errorMessage])
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
    // Simple file upload placeholder for now
    console.log("File upload feature coming soon!")
  }

  // Simple markdown renderer that handles line breaks
  const renderMessage = (text: string) => {
    // Convert **bold** to <strong>
    const withBold = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    
    // Split by lines and render each line
    const lines = withBold.split('\n')
    
    return (
      <div>
        {lines.map((line, index) => (
          <div key={index} className={index > 0 ? "mt-1" : ""}>
            {line ? (
              <span dangerouslySetInnerHTML={{ __html: line }} />
            ) : (
              <br />
            )}
          </div>
        ))}
      </div>
    )
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
                    <div className="whitespace-pre-wrap">
                      {renderMessage(message.text)}
                    </div>
                    
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
