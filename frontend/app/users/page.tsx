'use client'

import { useState, useEffect } from 'react'
import { usersApi, interestGroupsApi } from '@/lib/api'
import { User, UserCreate, UserUpdate, InterestGroup, UserGroupMembershipCreate } from '@/types'

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([])
  const [groups, setGroups] = useState<InterestGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [filterActive, setFilterActive] = useState<'all' | 'active' | 'inactive'>('all')
  
  // Modal states
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isMembershipModalOpen, setIsMembershipModalOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [usersResponse, groupsResponse] = await Promise.all([
        usersApi.list(),
        interestGroupsApi.list(),
      ])

      if (usersResponse.data) {
        setUsers(usersResponse.data)
      }
      if (groupsResponse.data) {
        setGroups(groupsResponse.data)
      }
      
      if (usersResponse.error) {
        setError(usersResponse.error)
      }
    } catch (err) {
      setError('Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateUser = async (userData: UserCreate) => {
    const response = await usersApi.create(userData)
    if (response.data) {
      setUsers([...users, response.data])
      setIsCreateModalOpen(false)
      setError('')
    } else {
      setError(response.error || 'Failed to create user')
    }
  }

  const handleUpdateUser = async (userId: number, userData: UserUpdate) => {
    const response = await usersApi.update(userId, userData)
    if (response.data) {
      setUsers(users.map(u => u.id === userId ? response.data! : u))
      setIsEditModalOpen(false)
      setSelectedUser(null)
      setError('')
    } else {
      setError(response.error || 'Failed to update user')
    }
  }

  const handleDeactivateUser = async (userId: number) => {
    if (!confirm('Möchtest du diesen Benutzer wirklich deaktivieren?')) return
    
    const response = await usersApi.deactivate(userId)
    if (response.data) {
      setUsers(users.map(u => u.id === userId ? response.data! : u))
      setError('')
    } else {
      setError(response.error || 'Failed to deactivate user')
    }
  }

  const handleReactivateUser = async (userId: number) => {
    const response = await usersApi.reactivate(userId)
    if (response.data) {
      setUsers(users.map(u => u.id === userId ? response.data! : u))
      setError('')
    } else {
      setError(response.error || 'Failed to reactivate user')
    }
  }

  // Filter and search logic
  const filteredUsers = users.filter(user => {
    const matchesSearch = 
      user.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.employee_id?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.organizational_unit?.toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesFilter = 
      filterActive === 'all' ||
      (filterActive === 'active' && user.is_active) ||
      (filterActive === 'inactive' && !user.is_active)
    
    return matchesSearch && matchesFilter
  })

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Benutzerverwaltung</h1>
          <p className="text-muted-foreground mt-1">
            Verwalte Benutzer, Rollen und Berechtigungen
          </p>
        </div>
        <button 
          onClick={() => setIsCreateModalOpen(true)}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors font-medium"
        >
          + Neuer Benutzer
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-md text-destructive flex items-start gap-2">
          <svg className="w-5 h-5 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <div>
            <p className="font-medium">Fehler</p>
            <p className="text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Search and Filters */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="Suche nach Name, Email, Mitarbeiter-ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-input rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
        </div>
        
        <div className="flex gap-2">
          <button
            onClick={() => setFilterActive('all')}
            className={`px-4 py-2 rounded-md font-medium transition-all duration-300 ${
              filterActive === 'all'
                ? 'bg-primary text-white shadow-sm'
                : 'bg-gray-100 text-gray-700 hover:bg-primary hover:text-white border border-gray-200'
            }`}
          >
            Alle ({users.length})
          </button>
          <button
            onClick={() => setFilterActive('active')}
            className={`px-4 py-2 rounded-md font-medium transition-all duration-300 ${
              filterActive === 'active'
                ? 'bg-primary text-white shadow-sm'
                : 'bg-gray-100 text-gray-700 hover:bg-primary hover:text-white border border-gray-200'
            }`}
          >
            Aktiv ({users.filter(u => u.is_active).length})
          </button>
          <button
            onClick={() => setFilterActive('inactive')}
            className={`px-4 py-2 rounded-md font-medium transition-all duration-300 ${
              filterActive === 'inactive'
                ? 'bg-primary text-white shadow-sm'
                : 'bg-gray-100 text-gray-700 hover:bg-primary hover:text-white border border-gray-200'
            }`}
          >
            Inaktiv ({users.filter(u => !u.is_active).length})
          </button>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50 border-b border-border">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Benutzer
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Mitarbeiter-ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Organisationseinheit
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Rolle
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Aktionen
                </th>
              </tr>
            </thead>
            <tbody className="bg-card divide-y divide-border">
              {filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-muted-foreground">
                    <svg className="mx-auto h-12 w-12 mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                    <p className="font-medium">Keine Benutzer gefunden</p>
                    <p className="text-sm mt-1">
                      {searchQuery ? 'Versuche einen anderen Suchbegriff' : 'Erstelle deinen ersten Benutzer'}
                    </p>
                  </td>
                </tr>
              ) : (
                filteredUsers.map((user) => (
                  <tr key={user.id} className="hover:bg-muted/50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10 bg-primary/10 rounded-full flex items-center justify-center">
                          <span className="text-primary font-medium text-sm">
                            {user.full_name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()}
                          </span>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-foreground">{user.full_name}</div>
                          <div className="text-sm text-muted-foreground">{user.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-foreground font-mono">
                        {user.employee_id || '-'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-foreground">
                        {user.organizational_unit || '-'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex flex-col gap-1">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          user.is_active
                            ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                            : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                        }`}>
                          {user.is_active ? 'Aktiv' : 'Inaktiv'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex flex-col gap-1">
                        {user.is_department_head && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
                            Abteilungsleiter
                          </span>
                        )}
                        {user.approval_level > 0 && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400">
                            Genehmigungslevel {user.approval_level}
                          </span>
                        )}
                        {!user.is_department_head && user.approval_level === 0 && (
                          <span className="text-sm text-muted-foreground">Mitarbeiter</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => {
                            setSelectedUser(user)
                            setIsMembershipModalOpen(true)
                          }}
                          className="text-primary hover:text-primary/80 font-medium"
                          title="Gruppenzugehörigkeit verwalten"
                        >
                          Gruppen
                        </button>
                        <button
                          onClick={() => {
                            setSelectedUser(user)
                            setIsEditModalOpen(true)
                          }}
                          className="text-primary hover:text-primary/80 font-medium"
                        >
                          Bearbeiten
                        </button>
                        {user.is_active ? (
                          <button
                            onClick={() => handleDeactivateUser(user.id)}
                            className="text-destructive hover:text-destructive/80 font-medium"
                          >
                            Deaktivieren
                          </button>
                        ) : (
                          <button
                            onClick={() => handleReactivateUser(user.id)}
                            className="text-green-600 hover:text-green-700 font-medium"
                          >
                            Reaktivieren
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Stats Footer */}
      <div className="mt-6 flex items-center justify-between text-sm text-muted-foreground">
        <div>
          Zeige {filteredUsers.length} von {users.length} Benutzern
        </div>
        <div className="flex gap-4">
          <div>
            <span className="font-medium text-foreground">{users.filter(u => u.is_active).length}</span> aktiv
          </div>
          <div>
            <span className="font-medium text-foreground">{users.filter(u => u.is_department_head).length}</span> Abteilungsleiter
          </div>
        </div>
      </div>

      {/* Modals */}
      {isCreateModalOpen && (
        <UserCreateModal
          onClose={() => setIsCreateModalOpen(false)}
          onCreate={handleCreateUser}
        />
      )}

      {isEditModalOpen && selectedUser && (
        <UserEditModal
          user={selectedUser}
          onClose={() => {
            setIsEditModalOpen(false)
            setSelectedUser(null)
          }}
          onUpdate={(data) => handleUpdateUser(selectedUser.id, data)}
        />
      )}

      {isMembershipModalOpen && selectedUser && (
        <UserMembershipModal
          user={selectedUser}
          groups={groups}
          onClose={() => {
            setIsMembershipModalOpen(false)
            setSelectedUser(null)
          }}
          onUpdate={fetchData}
        />
      )}
    </div>
  )
}

/* ========== CREATE USER MODAL ========== */
function UserCreateModal({ onClose, onCreate }: { onClose: () => void; onCreate: (data: UserCreate) => void }) {
  const [formData, setFormData] = useState<UserCreate>({
    email: '',
    full_name: '',
    password: '',
    employee_id: '',
    organizational_unit: '',
    is_department_head: false,
    approval_level: 0,
    individual_permissions: [],
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    await onCreate(formData)
    setIsSubmitting(false)
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={onClose}>
      <div className="bg-card rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="p-6 border-b border-border">
          <h2 className="text-2xl font-bold text-foreground">Neuen Benutzer erstellen</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Füge einen neuen Benutzer zum System hinzu
          </p>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Vollständiger Name *
              </label>
              <input
                type="text"
                required
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                className="w-full px-3 py-2 border border-input rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="Max Mustermann"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                E-Mail *
              </label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-3 py-2 border border-input rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="max.mustermann@example.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Passwort *
              </label>
              <input
                type="password"
                required
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="w-full px-3 py-2 border border-input rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="••••••••"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Mitarbeiter-ID
              </label>
              <input
                type="text"
                value={formData.employee_id}
                onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
                className="w-full px-3 py-2 border border-input rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="EMP-001"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-foreground mb-2">
                Organisationseinheit
              </label>
              <input
                type="text"
                value={formData.organizational_unit}
                onChange={(e) => setFormData({ ...formData, organizational_unit: e.target.value })}
                className="w-full px-3 py-2 border border-input rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="z.B. Qualitätsmanagement"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Genehmigungslevel
              </label>
              <select
                value={formData.approval_level}
                onChange={(e) => setFormData({ ...formData, approval_level: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-input rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value={0}>0 - Keine Genehmigung</option>
                <option value={1}>1 - Basis</option>
                <option value={2}>2 - Erweitert</option>
                <option value={3}>3 - Vollständig</option>
              </select>
            </div>

            <div className="flex items-center">
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_department_head}
                  onChange={(e) => setFormData({ ...formData, is_department_head: e.target.checked })}
                  className="w-4 h-4 text-primary border-input rounded focus:ring-ring focus:ring-2"
                />
                <span className="ml-2 text-sm font-medium text-foreground">
                  Abteilungsleiter
                </span>
              </label>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-border">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-input rounded-md hover:bg-accent transition-colors"
            >
              Abbrechen
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              {isSubmitting ? 'Erstelle...' : 'Benutzer erstellen'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

/* ========== EDIT USER MODAL ========== */
function UserEditModal({ user, onClose, onUpdate }: { user: User; onClose: () => void; onUpdate: (data: UserUpdate) => void }) {
  const [formData, setFormData] = useState<UserUpdate>({
    full_name: user.full_name,
    email: user.email,
    employee_id: user.employee_id,
    organizational_unit: user.organizational_unit,
    is_department_head: user.is_department_head,
    approval_level: user.approval_level,
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    await onUpdate(formData)
    setIsSubmitting(false)
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={onClose}>
      <div className="bg-card rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="p-6 border-b border-border">
          <h2 className="text-2xl font-bold text-foreground">Benutzer bearbeiten</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Aktualisiere die Benutzerdaten
          </p>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Vollständiger Name
              </label>
              <input
                type="text"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                className="w-full px-3 py-2 border border-input rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                E-Mail
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-3 py-2 border border-input rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Mitarbeiter-ID
              </label>
              <input
                type="text"
                value={formData.employee_id || ''}
                onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
                className="w-full px-3 py-2 border border-input rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Genehmigungslevel
              </label>
              <select
                value={formData.approval_level}
                onChange={(e) => setFormData({ ...formData, approval_level: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-input rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value={0}>0 - Keine Genehmigung</option>
                <option value={1}>1 - Basis</option>
                <option value={2}>2 - Erweitert</option>
                <option value={3}>3 - Vollständig</option>
              </select>
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-foreground mb-2">
                Organisationseinheit
              </label>
              <input
                type="text"
                value={formData.organizational_unit || ''}
                onChange={(e) => setFormData({ ...formData, organizational_unit: e.target.value })}
                className="w-full px-3 py-2 border border-input rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>

            <div className="flex items-center">
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_department_head}
                  onChange={(e) => setFormData({ ...formData, is_department_head: e.target.checked })}
                  className="w-4 h-4 text-primary border-input rounded focus:ring-ring focus:ring-2"
                />
                <span className="ml-2 text-sm font-medium text-foreground">
                  Abteilungsleiter
                </span>
              </label>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-border">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-input rounded-md hover:bg-accent transition-colors"
            >
              Abbrechen
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              {isSubmitting ? 'Speichere...' : 'Änderungen speichern'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

/* ========== USER MEMBERSHIP MODAL ========== */
function UserMembershipModal({ 
  user, 
  groups, 
  onClose, 
  onUpdate 
}: { 
  user: User
  groups: InterestGroup[]
  onClose: () => void
  onUpdate: () => void
}) {
  const [memberships, setMemberships] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedGroupId, setSelectedGroupId] = useState<number | ''>('')
  const [roleInGroup, setRoleInGroup] = useState('')
  const [approvalLevel, setApprovalLevel] = useState(0)

  useEffect(() => {
    fetchMemberships()
  }, [])

  const fetchMemberships = async () => {
    const response = await usersApi.getMemberships(user.id)
    if (response.data) {
      setMemberships(response.data)
    }
    setLoading(false)
  }

  const handleAddMembership = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedGroupId) return

    const data: UserGroupMembershipCreate = {
      user_id: user.id,
      interest_group_id: selectedGroupId as number,
      role_in_group: roleInGroup || undefined,
      approval_level: approvalLevel,
    }

    const response = await usersApi.addMembership(user.id, data)
    if (response.data) {
      await fetchMemberships()
      setSelectedGroupId('')
      setRoleInGroup('')
      setApprovalLevel(0)
      onUpdate()
    }
  }

  const handleRemoveMembership = async (groupId: number) => {
    if (!confirm('Möchtest du diese Gruppenzugehörigkeit wirklich entfernen?')) return
    
    const response = await usersApi.removeMembership(user.id, groupId)
    if (response.status === 204 || response.status === 200) {
      await fetchMemberships()
      onUpdate()
    }
  }

  const availableGroups = groups.filter(
    g => !memberships.some(m => m.interest_group_id === g.id)
  )

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={onClose}>
      <div className="bg-card rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="p-6 border-b border-border">
          <h2 className="text-2xl font-bold text-foreground">Gruppenzugehörigkeit verwalten</h2>
          <p className="text-sm text-muted-foreground mt-1">
            {user.full_name} - {user.email}
          </p>
        </div>
        
        <div className="p-6">
          {/* Add Membership Form */}
          {availableGroups.length > 0 && (
            <form onSubmit={handleAddMembership} className="mb-6 p-4 bg-muted/30 rounded-lg">
              <h3 className="font-medium text-foreground mb-3">Neue Gruppenzugehörigkeit hinzufügen</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Interest Group
                  </label>
                  <select
                    value={selectedGroupId}
                    onChange={(e) => setSelectedGroupId(e.target.value ? parseInt(e.target.value) : '')}
                    className="w-full px-3 py-2 border border-input rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
                    required
                  >
                    <option value="">Auswählen...</option>
                    {availableGroups.map(group => (
                      <option key={group.id} value={group.id}>
                        {group.name} ({group.code})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Rolle in Gruppe
                  </label>
                  <input
                    type="text"
                    value={roleInGroup}
                    onChange={(e) => setRoleInGroup(e.target.value)}
                    className="w-full px-3 py-2 border border-input rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
                    placeholder="z.B. Mitglied, Leiter"
                  />
                </div>
                <div className="flex items-end">
                  <button
                    type="submit"
                    className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
                  >
                    Hinzufügen
                  </button>
                </div>
              </div>
            </form>
          )}

          {/* Current Memberships */}
          <div>
            <h3 className="font-medium text-foreground mb-3">
              Aktuelle Gruppenzugehörigkeiten ({memberships.length})
            </h3>
            
            {loading ? (
              <div className="text-center py-8 text-muted-foreground">Lade...</div>
            ) : memberships.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <p>Noch keine Gruppenzugehörigkeiten</p>
              </div>
            ) : (
              <div className="space-y-2">
                {memberships.map((membership) => (
                  <div
                    key={membership.id}
                    className="flex items-center justify-between p-3 border border-border rounded-md hover:bg-muted/30 transition-colors"
                  >
                    <div className="flex-1">
                      <div className="font-medium text-foreground">
                        {membership.interest_group?.name || `Group ID ${membership.interest_group_id}`}
                      </div>
                      {membership.role_in_group && (
                        <div className="text-sm text-muted-foreground">
                          Rolle: {membership.role_in_group}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`px-2 py-1 text-xs rounded-full font-medium ${
                        membership.is_active
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                          : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                      }`}>
                        {membership.is_active ? 'Aktiv' : 'Inaktiv'}
                      </span>
                      <button
                        onClick={() => handleRemoveMembership(membership.interest_group_id)}
                        className="text-destructive hover:text-destructive/80 text-sm font-medium"
                      >
                        Entfernen
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="p-6 border-t border-border flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            Fertig
          </button>
        </div>
      </div>
    </div>
  )
}
