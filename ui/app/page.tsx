"use client"

import Link from "next/link"
import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import {
  CheckCircle,
  ChevronRight,
  MessageSquare,
  FileText,
  PlayCircle,
  User,
  Upload,
  Calendar,
  DollarSign,
  Activity,
} from "lucide-react"

export default function Home() {
  return (
    <div className="min-h-screen bg-cream-50">
      {/* Navigation */}
      <nav className="container mx-auto py-4 px-4 flex justify-between items-center">
        <div className="font-semibold text-xl text-teal-700">
          <span className="text-terracotta">Accessa</span> Medicare Navigator
        </div>
        <Button variant="ghost" size="icon" className="rounded-full bg-white shadow-sm">
          <User className="h-5 w-5 text-teal-700" />
          <span className="sr-only">Profile</span>
        </Button>
      </nav>

      {/* Hero Section */}
      <section className="py-16 md:py-24 relative">
        {/* Full-width watercolor background */}
        <div className="absolute inset-0 bg-cream-50">
          <div className="h-full w-full overflow-hidden">
            <Image
              src="/images/interface_banner.png"
              alt="Watercolor illustration of a medical facility in a serene landscape"
              fill
              className="object-cover object-center opacity-90"
              priority
            />
          </div>
        </div>

        {/* Content positioned with z-index to appear above the background */}
        <div className="container mx-auto px-4 relative z-10">
          <div className="max-w-3xl bg-white/80 backdrop-blur-sm p-8 rounded-2xl shadow-sm">
            <h1 className="text-4xl md:text-5xl font-bold text-teal-800 mb-6">Navigate Medicare with Confidence</h1>
            <p className="text-xl text-teal-700 mb-8">
              Get personalized questions to ask your doctor, understand your insurance plan, and feel more in control —
              all in one secure place.
            </p>
            <Button
              size="lg"
              className="bg-terracotta hover:bg-terracotta-600 text-white px-8 py-6 text-lg rounded-xl shadow-lg transition-all"
              onClick={() => window.open("/chat", "_blank")}
            >
              Start Now
              <ChevronRight className="ml-2 h-5 w-5" />
            </Button>
          </div>
        </div>
      </section>

      {/* Sample Output + How It Works */}
      <section className="container mx-auto px-4 py-16 bg-white rounded-t-3xl shadow-sm">
        <div className="grid md:grid-cols-2 gap-8 items-start">
          {/* Sample Output */}
          <div>
            <h2 className="text-3xl font-bold text-teal-800 mb-8">Sample Output</h2>
            <Card className="p-6 shadow-lg rounded-xl bg-white">
              <div className="mb-6 p-4 bg-sky-50 rounded-lg">
                <p className="text-teal-800 italic">
                  "I've been having lower back pain for a few weeks — what should I ask my doctor during my Medicare
                  visit?"
                </p>
              </div>
              <div className="space-y-6">
                <div className="border-l-4 border-teal-500 pl-4">
                  <h3 className="font-semibold text-teal-800 mb-2">What to track before your visit:</h3>
                  <ul className="space-y-2">
                    {["Symptoms", "Duration", "Patterns", "What helps or worsens", "Mobility changes"].map(
                      (item, i) => (
                        <li key={i} className="flex items-start">
                          <CheckCircle className="h-5 w-5 text-teal-500 mr-2 flex-shrink-0 mt-0.5" />
                          <span className="text-teal-700">{item}</span>
                        </li>
                      ),
                    )}
                  </ul>
                </div>
                <div className="border-l-4 border-sky-500 pl-4">
                  <h3 className="font-semibold text-teal-800 mb-2">Questions to ask your PCP:</h3>
                  <ul className="space-y-2">
                    {["Causes", "Medicare Part B coverage for imaging", "Exercises", "Red flag symptoms"].map(
                      (item, i) => (
                        <li key={i} className="flex items-start">
                          <CheckCircle className="h-5 w-5 text-sky-500 mr-2 flex-shrink-0 mt-0.5" />
                          <span className="text-teal-700">{item}</span>
                        </li>
                      ),
                    )}
                  </ul>
                </div>
                <div className="border-l-4 border-cream-500 pl-4">
                  <h3 className="font-semibold text-teal-800 mb-2">What to expect:</h3>
                  <ul className="space-y-2">
                    {["Referrals", "Coverage through Medicare Part B", "Next steps"].map((item, i) => (
                      <li key={i} className="flex items-start">
                        <CheckCircle className="h-5 w-5 text-cream-600 mr-2 flex-shrink-0 mt-0.5" />
                        <span className="text-teal-700">{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <p className="text-teal-700 italic mt-4 p-3 bg-cream-50 rounded-lg">
                  Some next steps may depend on what's covered with your Medicare Part B insurance.
                </p>
              </div>
            </Card>
          </div>

          {/* How It Works + Video */}
          <div>
            <h2 className="text-3xl font-bold text-teal-800 mb-8">How It Works</h2>
            <div className="space-y-6 mb-8">
              <div className="flex items-start p-4 bg-cream-50 rounded-xl">
                <div className="bg-cream-100 w-12 h-12 rounded-full flex items-center justify-center mr-4 flex-shrink-0">
                  <Upload className="h-6 w-6 text-teal-700" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-teal-800 mb-1">Step 1</h3>
                  <p className="text-teal-700">Upload your Medicare plan or start with a question</p>
                </div>
              </div>

              <div className="flex items-start p-4 bg-sky-50 rounded-xl">
                <div className="bg-sky-100 w-12 h-12 rounded-full flex items-center justify-center mr-4 flex-shrink-0">
                  <MessageSquare className="h-6 w-6 text-sky-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-teal-800 mb-1">Step 2</h3>
                  <p className="text-teal-700">Chat securely with our Medicare Navigator</p>
                </div>
              </div>

              <div className="flex items-start p-4 bg-teal-50 rounded-xl">
                <div className="bg-teal-100 w-12 h-12 rounded-full flex items-center justify-center mr-4 flex-shrink-0">
                  <FileText className="h-6 w-6 text-teal-700" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-teal-800 mb-1">Step 3</h3>
                  <p className="text-teal-700">Keep track of insights anytime</p>
                </div>
              </div>
            </div>

            {/* Video directly under How It Works */}
            <div className="aspect-w-16 aspect-h-9 bg-sky-50 rounded-xl overflow-hidden relative">
              <div className="absolute inset-0 flex items-center justify-center">
                <PlayCircle className="h-20 w-20 text-teal-700 opacity-80" />
              </div>
            </div>
            <p className="text-center text-teal-700 mt-4">See how Medicare Navigator helps you stay one step ahead.</p>
          </div>
        </div>
      </section>

      {/* What's Coming */}
      <section className="container mx-auto px-4 py-16 bg-gradient-to-b from-white to-cream-50">
        <h2 className="text-3xl font-bold text-center text-teal-800 mb-6">What's Coming</h2>
        <p className="text-center text-teal-700 mb-12 max-w-2xl mx-auto">
          More tools coming soon to help you plan, prepare, and follow up on care.
        </p>
        <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          <Card className="p-6 bg-white border border-teal-100 text-center rounded-xl shadow-sm hover:shadow-md transition-all">
            <div className="bg-sky-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
              <Calendar className="h-8 w-8 text-sky-600" />
            </div>
            <h3 className="text-xl font-semibold text-teal-800 mb-2">Doctor's Office Scheduling</h3>
            <p className="text-teal-700">
              Easily request appointments through Medicare Navigator, with scheduling and doctor research handled automatically through the chat.
            </p>
          </Card>

          <Card className="p-6 bg-white border border-teal-100 text-center rounded-xl shadow-sm hover:shadow-md transition-all">
            <div className="bg-cream-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
              <DollarSign className="h-8 w-8 text-terracotta" />
            </div>
            <h3 className="text-xl font-semibold text-teal-800 mb-2">Claim Evaluation and Filing</h3>
            <p className="text-teal-700">
              Optimize your healthcare benefits with our compliant assessment tools that help determine claim
              eligibility and streamline the filing process.
            </p>
          </Card>

          <Card className="p-6 bg-white border border-teal-100 text-center rounded-xl shadow-sm hover:shadow-md transition-all">
            <div className="bg-teal-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
              <Activity className="h-8 w-8 text-teal-600" />
            </div>
            <h3 className="text-xl font-semibold text-teal-800 mb-2">Symptom Tracking</h3>
            <p className="text-teal-700">
              Easily log and organize your symptoms through simple conversations, creating a clear record your doctor
              can review during visits.
            </p>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-teal-800 text-white py-12 px-4">
        <div className="container mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center mb-8">
            <div className="text-xl font-semibold mb-4 md:mb-0">
              <span className="text-terracotta-300">Accessa</span>
            </div>
            <div className="flex space-x-6">
              <Link href="/terms" target="_blank" className="text-cream-200 hover:text-white transition-colors">
                Terms
              </Link>
              <Link href="/privacy" target="_blank" className="text-cream-200 hover:text-white transition-colors">
                Privacy
              </Link>
            </div>
          </div>
          <div className="text-center text-teal-200 text-sm">
            Medicare Navigator is a platform built by Accessa to support better healthcare navigation.
          </div>
        </div>
      </footer>
    </div>
  )
}
