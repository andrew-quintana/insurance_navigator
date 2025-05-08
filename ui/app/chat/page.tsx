"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { SendHorizontal, ArrowLeft } from "lucide-react"

type Message = {
  id: number
  sender: "bot" | "user"
  text: string
  options?: string[]
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState("")
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Initial bot message when the chat loads
  useEffect(() => {
    const initialMessage: Message = {
      id: 1,
      sender: "bot",
      text: "Hello! I'm your Medicare Navigator. To get started, what type of Medicare coverage do you have?",
      options: [
        "Original Medicare (Part A & B)",
        "Medicare Advantage (Part C)",
        "Medicare Part D (Prescription)",
        "Medicare Supplement (Medigap)",
        "I'm not sure",
      ],
    }
    setMessages([initialMessage])
  }, [])

  // Auto-scroll to the bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Focus the input field when the component mounts
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const handleSendMessage = () => {
    if (inputValue.trim() === "") return

    // Add user message
    const userMessage: Message = {
      id: messages.length + 1,
      sender: "user",
      text: inputValue,
    }

    setMessages((prevMessages) => [...prevMessages, userMessage])
    setInputValue("")

    // Simulate bot response after user sends a message
    setTimeout(() => {
      const botResponse: Message = {
        id: messages.length + 2,
        sender: "bot",
        text: "Thank you for sharing your Medicare coverage information. This helps me provide more personalized guidance for your healthcare questions. What can I help you with today?",
      }
      setMessages((prevMessages) => [...prevMessages, botResponse])
    }, 1000)
  }

  const handleOptionClick = (option: string) => {
    // Add user message with the selected option
    const userMessage: Message = {
      id: messages.length + 1,
      sender: "user",
      text: option,
    }

    setMessages((prevMessages) => [...prevMessages, userMessage])

    // Simulate bot response after option selection
    setTimeout(() => {
      const botResponse: Message = {
        id: messages.length + 2,
        sender: "bot",
        text: `Thank you for letting me know you have ${option}. This helps me provide more personalized guidance for your healthcare questions. What can I help you with today?`,
      }
      setMessages((prevMessages) => [...prevMessages, botResponse])
    }, 1000)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSendMessage()
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
          <h1 className="text-xl font-semibold text-teal-800 mx-auto pr-8">Medicare Navigator Chat</h1>
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
                    <p>{message.text}</p>
                    {message.options && (
                      <div className="mt-4 flex flex-wrap gap-2">
                        {message.options.map((option, index) => (
                          <Button
                            key={index}
                            variant="outline"
                            className="bg-white text-teal-700 border-teal-300 hover:bg-teal-50 hover:text-teal-800 mt-1"
                            onClick={() => handleOptionClick(option)}
                          >
                            {option}
                          </Button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input Area */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center">
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your message here..."
                className="flex-1 p-3 border border-gray-300 rounded-l-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
              <Button
                onClick={handleSendMessage}
                className="bg-teal-700 hover:bg-teal-800 text-white rounded-r-lg p-3 h-[46px]"
              >
                <SendHorizontal className="h-5 w-5" />
              </Button>
            </div>
          </div>
        </Card>

        {/* Info Card */}
        <Card className="p-4 bg-sky-50 text-teal-800 text-sm rounded-xl">
          <p className="font-medium">Privacy Note</p>
          <p className="mt-1">
            Your Medicare information is kept secure and private. We only use this information to provide personalized
            guidance for your healthcare questions.
          </p>
        </Card>
      </div>
    </div>
  )
}
