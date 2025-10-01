'use client'

import UserMatrixView from '@/app/components/UserMatrixView'

/**
 * 👥 User Management Page
 * 
 * Zeigt User × Interest Groups Matrix für schnelles Zuweisen von Permissions
 */

export default function UsersPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground">User Management</h1>
        <p className="text-muted-foreground mt-2">
          Manage user permissions across interest groups
        </p>
      </div>

      {/* Matrix View */}
      <UserMatrixView />
    </div>
  )
}

