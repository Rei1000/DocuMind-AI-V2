import Link from 'next/link'

export default function Home() {
  return (
    <main className="bg-gradient-to-b from-gray-50 to-white min-h-screen">
      {/* Hero Section */}
      <div className="container mx-auto px-6 py-16">
        <div className="text-center max-w-4xl mx-auto">
          <div className="mb-8">
            <img 
              src="/logo.png" 
              alt="DocuMind-AI" 
              className="h-24 w-auto mx-auto mb-6"
            />
          </div>
          <h1 className="text-5xl font-bold text-gray-900 mb-4 tracking-tight">
            Medical Knowledge Management
          </h1>
          <p className="text-xl text-gray-600 mb-8 leading-relaxed">
            Professionelles Quality Management System für Healthcare<br/>
            <span className="text-sm font-medium text-primary">ISO 13485 Compliant • DDD Architecture • Enterprise Ready</span>
          </p>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto mt-16">
          <Link 
            href="/login" 
            className="group bg-white p-8 rounded-xl border-2 border-gray-200 hover:border-primary hover:shadow-lg transition-all duration-300"
          >
            <div className="text-4xl mb-4 group-hover:scale-110 transition-transform">🔐</div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">Login</h2>
            <p className="text-gray-600 text-sm">
              Sichere Authentifizierung für Ihr Team
            </p>
          </Link>
          
          <Link 
            href="/users" 
            className="group bg-white p-8 rounded-xl border-2 border-gray-200 hover:border-primary hover:shadow-lg transition-all duration-300"
          >
            <div className="text-4xl mb-4 group-hover:scale-110 transition-transform">👥</div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">Benutzer</h2>
            <p className="text-gray-600 text-sm">
              Verwaltung von Rollen & Berechtigungen
            </p>
          </Link>
          
          <Link 
            href="/interest-groups" 
            className="group bg-white p-8 rounded-xl border-2 border-gray-200 hover:border-primary hover:shadow-lg transition-all duration-300"
          >
            <div className="text-4xl mb-4 group-hover:scale-110 transition-transform">🏢</div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">Stakeholder</h2>
            <p className="text-gray-600 text-sm">
              13 Interest Groups Management
            </p>
          </Link>
          
          <Link 
            href="/models" 
            className="group bg-white p-8 rounded-xl border-2 border-gray-200 hover:border-primary hover:shadow-lg transition-all duration-300"
          >
            <div className="text-4xl mb-4 group-hover:scale-110 transition-transform">🤖</div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">AI Models</h2>
            <p className="text-gray-600 text-sm">
              OCR & Vision AI Integration
            </p>
          </Link>
        </div>
      </div>
    </main>
  )
}
