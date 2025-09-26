import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { ErrorBoundary } from "@/components/error-boundary"
import { AuthProvider } from "@/components/auth/SessionManager"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: {
    default: "Insurance Navigator",
    template: "%s | Insurance Navigator"
  },
  description:
    "Navigate Medicare with confidence. Get personalized questions to ask your doctor, understand your insurance plan, and feel more in control.",
  keywords: [
    "Medicare",
    "Healthcare",
    "Insurance",
    "Navigation",
    "Medical Questions",
    "Healthcare Planning",
    "Insurance Navigator"
  ],
  authors: [{ name: "Insurance Navigator" }],
  creator: "Insurance Navigator",
  publisher: "Insurance Navigator",
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'),
  alternates: {
    canonical: '/',
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
    title: 'Insurance Navigator',
    description: 'Navigate Medicare with confidence. Get personalized questions to ask your doctor, understand your insurance plan, and feel more in control.',
    siteName: 'Insurance Navigator',
    images: [
      {
        url: '/images/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Insurance Navigator',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Insurance Navigator',
    description: 'Navigate Medicare with confidence. Get personalized questions to ask your doctor, understand your insurance plan, and feel more in control.',
    images: ['/images/twitter-image.png'],
    creator: '@insurancenavigator',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  verification: {
    google: process.env.NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION,
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ErrorBoundary>
          <AuthProvider>
            <ThemeProvider 
              attribute="class" 
              defaultTheme={process.env.NEXT_PUBLIC_DEFAULT_THEME || "light"} 
              enableSystem 
              disableTransitionOnChange
            >
              {children}
            </ThemeProvider>
          </AuthProvider>
        </ErrorBoundary>
        
        {/* Google Analytics */}
        {process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS_ID && (
          <>
            <script
              async
              src={`https://www.googletagmanager.com/gtag/js?id=${process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS_ID}`}
            />
            <script
              dangerouslySetInnerHTML={{
                __html: `
                  window.dataLayer = window.dataLayer || [];
                  function gtag(){dataLayer.push(arguments);}
                  gtag('js', new Date());
                  gtag('config', '${process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS_ID}', {
                    page_title: document.title,
                    page_location: window.location.href,
                  });
                `,
              }}
            />
          </>
        )}
        
        {/* Hotjar Analytics */}
        {process.env.NEXT_PUBLIC_HOTJAR_ID && (
          <script
            dangerouslySetInnerHTML={{
              __html: `
                (function(h,o,t,j,a,r){
                  h.hj=h.hj||function(){(h.hj.q=h.hj.q||[]).push(arguments)};
                  h._hjSettings={hjid:${process.env.NEXT_PUBLIC_HOTJAR_ID},hjsv:6};
                  a=o.getElementsByTagName('head')[0];
                  r=o.createElement('script');r.async=1;
                  r.src=t+h._hjSettings.hjid+j+h._hjSettings.hjsv;
                  a.appendChild(r);
                })(window,document,'https://static.hotjar.com/c/hotjar-','.js?sv=');
              `,
            }}
          />
        )}
        
        {/* Maintenance mode overlay */}
        {process.env.NEXT_PUBLIC_MAINTENANCE_MODE === 'true' && (
          <div className="fixed inset-0 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-50">
            <div className="container flex h-screen w-screen flex-col items-center justify-center text-center">
              <h1 className="text-2xl font-semibold">Site Under Maintenance</h1>
              <p className="text-muted-foreground mt-2">
                We&apos;re currently performing scheduled maintenance. Please check back soon.
              </p>
            </div>
          </div>
        )}
      </body>
    </html>
  )
}
