import React from "react"
import Link from "next/link"
import { Github } from "lucide-react"

export default function Footer() {
  return (
    <footer className="bg-teal-800 text-white py-8 px-4 mt-auto">
      <div className="container mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
          <div className="text-lg font-semibold">
            <span className="text-terracotta-300">Insurance Navigator</span>
          </div>
          
          <div className="flex items-center space-x-6">
            <Link 
              href="/terms" 
              target="_blank" 
              className="text-cream-200 hover:text-white transition-colors"
            >
              Terms
            </Link>
            <Link 
              href="/privacy" 
              target="_blank" 
              className="text-cream-200 hover:text-white transition-colors"
            >
              Privacy
            </Link>
            <Link 
              href="https://github.com/andrew-quintana/insurance_navigator"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center text-cream-200 hover:text-white transition-colors"
            >
              <Github className="h-4 w-4 mr-2" />
              GitHub
            </Link>
          </div>
        </div>
        
        <div className="text-center text-teal-200 text-sm mt-4">
          Insurance Navigator is a platform built to support better healthcare navigation.
        </div>
      </div>
    </footer>
  )
}
