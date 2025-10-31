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
    <div className="max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">User Management</h1>
        <p className="text-gray-600">
          Drag groups onto users to assign permissions
        </p>
      </div>

      {/* User Management View */}
      <UserManagementView />
    </div>
  )
}

