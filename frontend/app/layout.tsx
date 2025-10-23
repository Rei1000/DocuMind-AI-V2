import type { Metadata } from 'next'
import { Open_Sans } from 'next/font/google'
import './globals.css'
import Navigation from './components/Navigation'
import { Toaster } from 'react-hot-toast'

const openSans = Open_Sans({ 
  weight: ['400', '500', '600', '700'],
  subsets: ['latin'],
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'DocuMind-AI | Medical Knowledge Management',
  description: 'Professional Quality Management System for Healthcare - ISO 13485 Compliant',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="de">
      <body className={openSans.className}>
        <div className="min-h-screen bg-background">
          <Navigation />
          <main>
            {children}
          </main>
          <Toaster 
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
              success: {
                duration: 3000,
                iconTheme: {
                  primary: '#4ade80',
                  secondary: '#fff',
                },
              },
              error: {
                duration: 5000,
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#fff',
                },
              },
            }}
          />
        </div>
      </body>
    </html>
  )
}
