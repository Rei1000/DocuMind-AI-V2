import Link from 'next/link'

export default function Home() {
  return (
    <main className="container mx-auto px-4 py-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-foreground mb-4">
          DocuMind-AI
        </h1>
        <p className="text-xl text-muted-foreground mb-8">
          Enterprise Quality Management System
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-4xl mx-auto">
          <Link 
            href="/login" 
            className="p-6 border rounded-lg hover:bg-accent transition-colors"
          >
            <h2 className="text-xl font-semibold mb-2">Login</h2>
            <p className="text-muted-foreground">
              Authenticate with the system
            </p>
          </Link>
          
          <Link 
            href="/models" 
            className="p-6 border rounded-lg hover:bg-accent transition-colors"
          >
            <h2 className="text-xl font-semibold mb-2">AI Models</h2>
            <p className="text-muted-foreground">
              Manage AI models and configurations
            </p>
          </Link>
          
          <Link 
            href="/interest-groups" 
            className="p-6 border rounded-lg hover:bg-accent transition-colors"
          >
            <h2 className="text-xl font-semibold mb-2">Interest Groups</h2>
            <p className="text-muted-foreground">
              Manage stakeholder groups
            </p>
          </Link>
        </div>
      </div>
    </main>
  )
}
