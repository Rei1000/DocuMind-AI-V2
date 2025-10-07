'use client'

import UserManagementView from '@/app/components/UserManagementView'

/**
 * 👥 User Management Page
 * 
 * 2-Column Layout:
 * - User Cards (left) with Interest Group Badges
 * - Interest Groups Sidebar (right) - draggable onto users
 */

export default function UsersPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-foreground">User Management</h1>
        <p className="text-muted-foreground mt-2">
          Drag groups onto users to assign permissions
        </p>
      </div>

      {/* User Management View */}
      <UserManagementView />
    </div>
  )
}

