"use client"

import React, { useState, useEffect, useRef } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { SendHorizontal, ArrowLeft, Upload, User } from "lucide-react"
import DocumentUploadModal from "@/components/DocumentUploadModal"
import WorkflowStatus from "@/components/WorkflowStatus"
// import { RealtimeChannel } from '@supabase/supabase-js'
import { useAuth } from "@/components/auth/SessionManager"

type Message = {
  id: number
  sender: "bot" | "user"
  text: string
  options?: string[]
  metadata?: Record<string, unknown>
  workflow_type?: string
}


export default function ChatPage() {
  const router = useRouter()
  const { user, loading, signOut } = useAuth()
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      sender: "bot",
      text: "Hello! I'm your Insurance Navigator assistant. I'm here to help you understand your insurance benefits and navigate insurance questions.\n\n**How can I assist you today?**",
      options: [
        "What is a copay?",
        "What is my deductible?",
        "How would I get access to mental health services?",
        "Am I covered for ambulances?",
        "What is a standard vs non-standard imaging procedure?"
      ]
    }
  ])
  const [inputValue, setInputValue] = useState("")
  const [conversationId] = useState<string>("")
  const [isLoading, setIsLoading] = useState(false)
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
  const [currentWorkflowId, setCurrentWorkflowId] = useState<string | null>(null)
  const [showWorkflowStatus, setShowWorkflowStatus] = useState(false)

  // Channel reference to prevent multiple subscriptions (currently unused)
  // const channelRef = useRef<RealtimeChannel | null>(null)
  
  // Refs for DOM elements
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const lastActivityTime = useRef<number>(Date.now())

  // Check authentication and redirect if not authenticated
  useEffect(() => {
    if (!loading && !user) {
      router.push("/login")
    }
  }, [loading, user, router])

  // Update initial message with user's name when authenticated
  useEffect(() => {
    if (user && messages.length === 1) {
      const userName = user.user_metadata?.full_name || user.email || 'there'
      const initialMessage: Message = {
        id: 1,
        sender: "bot",
        text: `Hello ${userName}! I'm your Insurance Navigator. I can help you with insurance questions, find healthcare providers, understand your benefits, and more. What would you like to know today?`,
        options: [
          "What is a copay?",
          "What is my deductible?",
          "How would I get access to mental health services?",
          "Am I covered for ambulances?",
          "What is a standard vs non-standard imaging procedure?"
        ]
      }
      setMessages([initialMessage])
    }
  }, [user, messages.length])

  // Track user activity for session management
  const updateActivity = () => {
    lastActivityTime.current = Date.now()
  }

  // TODO: Document status polling temporarily disabled due to API endpoint issues
  // This will be re-enabled once the /api/v2/jobs endpoint is properly implemented
  // For now, uploads work correctly but status notifications are not shown
  // Technical debt: Implement proper job status polling for document completion notifications

  // Auto-scroll to the bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Focus the input field when the component mounts
  useEffect(() => {
    if (user && inputRef.current) {
      inputRef.current.focus()
    }
  }, [user])

  const handleLogout = async () => {
    await signOut()
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
    
    // Generate a temporary workflow ID for immediate WebSocket connection
    const tempWorkflowId = `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setCurrentWorkflowId(tempWorkflowId);
    setShowWorkflowStatus(true);

    // Get API URL from environment variables (Vercel best practice)
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
    const chatUrl = `${apiBaseUrl}/chat`
    const token = localStorage.getItem("token")
    
    console.log("🌐 API Base URL:", apiBaseUrl)
    console.log("🔗 Chat URL:", chatUrl)

    try {
      const response = await fetch(chatUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          message: messageText,
          conversation_id: conversationId,
        }),
      })

      if (response.ok) {
        const data: { 
          text: string; 
          workflow_id?: string;
          metadata?: {
            workflow_tracking?: {
              workflow_id?: string;
              websocket_endpoint?: string;
            }
          }
        } = await response.json()
        
        // Update with real workflow_id if available
        const workflowId = data.workflow_id || data.metadata?.workflow_tracking?.workflow_id;
        if (workflowId && workflowId !== currentWorkflowId) {
          console.log("🔄 Real Workflow ID received:", workflowId);
          setCurrentWorkflowId(workflowId);
        }
        
        // Hide workflow status after response is received
        setTimeout(() => {
          setShowWorkflowStatus(false);
          setCurrentWorkflowId(null);
        }, 1000);
        
        const botMessage: Message = {
          id: messages.length + 2,
          text: data.text || "I received your message but couldn't generate a response.",
          sender: "bot",
        }
        setMessages(prev => [...prev, botMessage])
      } else {
        throw new Error(`Failed to get response: ${response.status}`)
      }
    } catch (error) {
      console.error("Chat error:", error)
      const errorMessage: Message = {
        id: messages.length + 2,
        text: "I'm sorry, I'm having trouble connecting right now. Please try again in a moment.",
        sender: "bot",
      }
      setMessages(prev => [...prev, errorMessage])
      
      // Hide workflow status on error
      setShowWorkflowStatus(false);
      setCurrentWorkflowId(null);
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
    updateActivity() // Track activity
    setIsUploadModalOpen(true)
  }

  const handleUploadSuccess = (result: { filename: string }) => {
    console.log('Upload successful:', result)
    
    // Add a message to the chat indicating successful upload
    const successMessage: Message = {
      id: messages.length + 1,
      text: `✅ **Document Upload Complete!**\n\nYour document "${result.filename}" has been uploaded successfully.`,
      sender: "bot"
    }
    
    setMessages(prev => [...prev, successMessage])
    setIsUploadModalOpen(false)
  }

  const handleUploadError = (error: string) => {
    console.error('Upload failed:', error)
    
    // Add an error message to the chat
    const errorMessage: Message = {
      id: messages.length + 1,
      text: `❌ **Document upload failed**\n\nI'm sorry, but there was an issue uploading your document: ${error}\n\nPlease try again or contact support if the problem persists.`,
      sender: "bot"
    }
    
    setMessages(prev => [...prev, errorMessage])
  }

  // Simple markdown renderer that handles line breaks
  const renderMessage = (text: string) => {
    // Add null safety
    if (!text || typeof text !== 'string') {
      return <div>Message content unavailable</div>
    }
    
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
  if (loading) {
    return (
      <div className="min-h-screen bg-cream-50 flex items-center justify-center">
        <Card className="p-8 bg-white rounded-xl shadow-md max-w-md">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-teal-800 mb-4">Loading Medicare Navigator...</h2>
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-700 mx-auto"></div>
            <p className="text-gray-600 mt-4 text-sm">Verifying your session...</p>
          </div>
        </Card>
      </div>
    )
  }

  // Show error screen if not authenticated
  if (!user) {
    return (
      <div className="min-h-screen bg-cream-50 flex items-center justify-center">
        <Card className="p-8 bg-white rounded-xl shadow-md max-w-md">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-teal-800 mb-4">Authentication Required</h2>
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
    <div className="flex-1 bg-cream-50 flex flex-col">
      {/* Upload Modal */}
      <DocumentUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadSuccess={handleUploadSuccess}
        onUploadError={handleUploadError}
      />

      {/* Header */}
      <header className="bg-white shadow-sm p-4">
        <div className="container mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center text-teal-700 hover:text-teal-800 transition-colors">
            <ArrowLeft className="h-5 w-5 mr-2" />
            <span>Return to Home</span>
          </Link>
          <h1 className="text-xl font-semibold text-teal-800">Insurance Navigator Chat</h1>
          <div className="flex items-center space-x-4">
            <div className="flex items-center text-teal-700">
              <User className="h-5 w-5 mr-2" />
              <span className="text-sm">{user?.user_metadata?.full_name || user?.email}</span>
            </div>
            <Button
              onClick={handleLogout}
              variant="outline"
              className="text-teal-700 border-teal-300 hover:bg-teal-50"
            >
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 flex">
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
                
                {/* Workflow Status */}
                {showWorkflowStatus && currentWorkflowId && user && (
                  <div className="flex justify-center mb-4">
                    <WorkflowStatus
                      workflowId={currentWorkflowId}
                      userId={user.id}
                      onComplete={() => {
                        setShowWorkflowStatus(false);
                        setCurrentWorkflowId(null);
                      }}
                      onError={(error) => {
                        console.error("WorkflowStatus error:", error);
                        setShowWorkflowStatus(false);
                        setCurrentWorkflowId(null);
                      }}
                    />
                  </div>
                )}

                {/* Loading indicator */}
                {isLoading && !showWorkflowStatus && (
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

        </div>
      </div>
    </div>
  )
}
