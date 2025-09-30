import type { Metadata } from 'next'
import { IBM_Plex_Sans } from 'next/font/google'
import './globals.css'
import Navigation from './components/Navigation'

const ibmPlexSans = IBM_Plex_Sans({ 
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
      <body className={ibmPlexSans.className}>
        <div className="min-h-screen bg-background">
          <Navigation />
          <main>
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
