'use client'

import { useState, useEffect } from 'react'
import { usersApi, interestGroupsApi } from '@/lib/api'
import { User, InterestGroup, UserGroupMembership } from '@/types'

/**
 * 🎨 Modern User Management - 2-Column Layout
 * 
 * Features:
 * - User Cards (left) mit Interest Group Badges
 * - Interest Groups Sidebar (right) - draggable
 * - Drag & Drop: Group → User
 * - Search + Filter
 * - Edit/Deactivate Users
 */

// Level Colors & Names
const LEVEL_COLORS = {
  1: 'bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200',
  2: 'bg-blue-100 text-blue-700 border-blue-300 hover:bg-blue-200',
  3: 'bg-orange-100 text-orange-700 border-orange-300 hover:bg-orange-200',
  4: 'bg-green-100 text-green-700 border-green-300 hover:bg-green-200',
  5: 'bg-purple-100 text-purple-700 border-purple-300 hover:bg-purple-200'
}

const LEVEL_NAMES = {
  1: 'Mitarbeiter',
  2: 'Teamleiter',
  3: 'Abteilungsleiter',
  4: 'QM-Manager',
  5: 'QMS Admin'
}

interface UserWithMemberships extends User {
  memberships: UserGroupMembership[]
}

export default function UserManagementView() {
  const [users, setUsers] = useState<UserWithMemberships[]>([])
  const [groups, setGroups] = useState<InterestGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  
  // Filter State
  const [searchQuery, setSearchQuery] = useState('')
  const [filterActive, setFilterActive] = useState<'all' | 'active' | 'inactive'>('all')
  const [filterGroup, setFilterGroup] = useState<number | null>(null)
  
  // Interest Groups Filter State
  const [groupSearchQuery, setGroupSearchQuery] = useState('')
  const [groupFilterActive, setGroupFilterActive] = useState<'all' | 'active' | 'inactive'>('all')
  
  // Modal States
  const [showLevelModal, setShowLevelModal] = useState(false)
  const [showEditUserModal, setShowEditUserModal] = useState(false)
  const [showCreateUserModal, setShowCreateUserModal] = useState(false)
  const [showEditGroupModal, setShowEditGroupModal] = useState(false)
  const [showCreateGroupModal, setShowCreateGroupModal] = useState(false)
  
  // New User Form State
  const [newUser, setNewUser] = useState({
    email: '',
    full_name: '',
    password: '',
    employee_id: '',
    organizational_unit: '',
  })
  
  // New Group Form State
  const [newGroup, setNewGroup] = useState({
    name: '',
    code: '',
    description: '',
    is_external: false,
  })
  
  // Edit Group Form State
  const [editGroup, setEditGroup] = useState({
    name: '',
    code: '',
    description: '',
    is_external: false,
    is_active: true,
  })
  
  const [selectedUser, setSelectedUser] = useState<UserWithMemberships | null>(null)
  const [selectedGroup, setSelectedGroup] = useState<InterestGroup | null>(null)
  const [selectedMembership, setSelectedMembership] = useState<UserGroupMembership | null>(null)
  const [selectedLevel, setSelectedLevel] = useState(1)
  
  // Drag State
  const [draggedGroup, setDraggedGroup] = useState<InterestGroup | null>(null)
  const [dragOverUser, setDragOverUser] = useState<number | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      
      // Load Users & Groups
      const [usersResp, groupsResp] = await Promise.all([
        usersApi.list(),
        interestGroupsApi.list()
      ])

      if (usersResp.data) {
        // Load memberships for each user
        const usersWithMemberships = await Promise.all(
          usersResp.data.map(async (user) => {
            const membershipResp = await usersApi.getMemberships(user.id)
            return {
              ...user,
              memberships: membershipResp.data || []
            }
          })
        )
        setUsers(usersWithMemberships)
      }

      if (groupsResp.data) {
        setGroups(groupsResp.data)
      }

      setError('')
    } catch (err) {
      setError('Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  // Filter Users
  const filteredUsers = users.filter(user => {
    // Search
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      if (!user.full_name.toLowerCase().includes(query) && 
          !user.email.toLowerCase().includes(query)) {
        return false
      }
    }
    
    // Active Filter
    if (filterActive === 'active' && !user.is_active) return false
    if (filterActive === 'inactive' && user.is_active) return false
    
    // Group Filter
    if (filterGroup) {
      if (!user.memberships.some(m => m.interest_group_id === filterGroup)) {
        return false
      }
    }
    
    return true
  })

  // Filter Interest Groups
  const filteredGroups = groups.filter(group => {
    // Search
    if (groupSearchQuery) {
      const query = groupSearchQuery.toLowerCase()
      if (!group.name.toLowerCase().includes(query) && 
          !group.code.toLowerCase().includes(query)) {
        return false
      }
    }
    
    // Active Filter
    if (groupFilterActive === 'active' && !group.is_active) return false
    if (groupFilterActive === 'inactive' && group.is_active) return false
    
    return true
  })

  // Drag & Drop Handlers
  const handleDragStart = (group: InterestGroup) => {
    setDraggedGroup(group)
  }

  const handleDragOver = (e: React.DragEvent, userId: number) => {
    e.preventDefault()
    setDragOverUser(userId)
  }

  const handleDragLeave = () => {
    setDragOverUser(null)
  }

  const handleDrop = async (user: UserWithMemberships) => {
    if (!draggedGroup) return

    setDragOverUser(null)
    
    // Check if already has membership
    const existing = user.memberships.find(m => m.interest_group_id === draggedGroup.id)
    
    if (existing) {
      // Edit existing
      setSelectedUser(user)
      setSelectedGroup(draggedGroup)
      setSelectedMembership(existing)
      setSelectedLevel(existing.approval_level)
      setShowLevelModal(true)
    } else {
      // Add new
      setSelectedUser(user)
      setSelectedGroup(draggedGroup)
      setSelectedMembership(null)
      setSelectedLevel(1)
      setShowLevelModal(true)
    }
    
    setDraggedGroup(null)
  }

  const handleBadgeClick = (user: UserWithMemberships, membership: UserGroupMembership) => {
    const group = groups.find(g => g.id === membership.interest_group_id)
    if (!group) return
    
    setSelectedUser(user)
    setSelectedGroup(group)
    setSelectedMembership(membership)
    setSelectedLevel(membership.approval_level)
    setShowLevelModal(true)
  }

  const handleSaveMembership = async () => {
    if (!selectedUser || !selectedGroup) return

    try {
      // Remove old if exists (WICHTIG: Warten bis fertig!)
      if (selectedMembership) {
        const removeResponse = await usersApi.removeMembership(selectedUser.id, selectedGroup.id)
        if (!removeResponse.data && removeResponse.error) {
          setError(`Failed to remove old membership: ${removeResponse.error}`)
          return
        }
        // Kurz warten damit DB-Transaktion fertig ist
        await new Promise(resolve => setTimeout(resolve, 300))
      }

      // Add new
      const addResponse = await usersApi.addMembership(selectedUser.id, {
        user_id: selectedUser.id,  // Backend braucht das!
        interest_group_id: selectedGroup.id,
        approval_level: selectedLevel,
        role_in_group: LEVEL_NAMES[selectedLevel as keyof typeof LEVEL_NAMES],
        is_department_head: selectedLevel >= 3,
      })

      if (!addResponse.data && addResponse.error) {
        setError(`Failed to add membership: ${addResponse.error}`)
        return
      }

      await loadData()
      setShowLevelModal(false)
      setSelectedUser(null)
      setSelectedGroup(null)
      setSelectedMembership(null)
      setError('')
    } catch (err) {
      setError('Failed to save membership')
    }
  }

  const handleRemoveMembership = async () => {
    if (!selectedUser || !selectedGroup || !selectedMembership) return

    try {
      await usersApi.removeMembership(selectedUser.id, selectedGroup.id)
      await loadData()
      setShowLevelModal(false)
      setSelectedUser(null)
      setSelectedGroup(null)
      setSelectedMembership(null)
    } catch (err) {
      setError('Failed to remove membership')
    }
  }

  const handleDeactivateUser = async (userId: number) => {
    if (!confirm('User wirklich deaktivieren?')) return
    
    try {
      await usersApi.deactivate(userId)
      await loadData()
    } catch (err) {
      setError('Failed to deactivate user')
    }
  }

  const handleReactivateUser = async (userId: number) => {
    try {
      await usersApi.reactivate(userId)
      await loadData()
    } catch (err) {
      setError('Failed to reactivate user')
    }
  }

  const handleToggleGroupActive = async (groupId: number, groupName: string, currentStatus: boolean) => {
    const action = currentStatus ? 'deaktivieren' : 'aktivieren'
    if (!confirm(`Interest Group "${groupName}" wirklich ${action}?`)) return
    
    try {
      await interestGroupsApi.update(groupId, { is_active: !currentStatus })
      await loadData()
    } catch (err) {
      setError(`Failed to ${action} interest group`)
    }
  }

  const handleCreateGroup = async () => {
    try {
      if (!newGroup.name || !newGroup.code) {
        setError('Name und Code sind erforderlich')
        return
      }

      // Code bereinigen (nur Leerzeichen durch Unterstriche ersetzen)
      const cleanCode = newGroup.code.replace(/\s+/g, '_')
      
      const response = await interestGroupsApi.create({
        name: newGroup.name,
        code: cleanCode,
        description: newGroup.description || undefined,
        is_external: newGroup.is_external,
      })
      
      if (response.data) {
        await loadData()
        setShowCreateGroupModal(false)
        setNewGroup({
          name: '',
          code: '',
          description: '',
          is_external: false,
        })
        setError('')
      } else {
        setError(response.error || 'Failed to create interest group')
      }
    } catch (err) {
      setError('Failed to create interest group')
    }
  }

  const handleEditGroup = async () => {
    if (!selectedGroup) return
    
    try {
      if (!editGroup.name || !editGroup.code) {
        setError('Name und Code sind erforderlich')
        return
      }

      // Code bereinigen (nur Leerzeichen durch Unterstriche ersetzen)
      const cleanCode = editGroup.code.replace(/\s+/g, '_')
      
      const response = await interestGroupsApi.update(selectedGroup.id, {
        name: editGroup.name,
        code: cleanCode,
        description: editGroup.description || undefined,
        is_external: editGroup.is_external,
        is_active: editGroup.is_active,
      })
      
      if (response.data) {
        await loadData()
        setShowEditGroupModal(false)
        setSelectedGroup(null)
        setError('')
      } else {
        setError(response.error || 'Failed to update interest group')
      }
    } catch (err) {
      setError('Failed to update interest group')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="text-lg font-semibold mb-2">Loading...</div>
          <div className="text-sm text-muted-foreground">Fetching users and groups...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex gap-6 h-full">
        {/* LEFT: Users (60%) */}
        <div className="flex-1 space-y-4">
        {/* Search & Filter */}
        <div className="bg-white p-4 rounded-lg border border-gray-200 space-y-4">
          <div className="flex gap-4">
            <input
              type="text"
              placeholder="🔍 Search users (name, email)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <button 
              onClick={() => setShowCreateUserModal(true)}
              className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90 transition-colors"
            >
              ➕ Create User
            </button>
          </div>

          <div className="flex gap-4 flex-wrap">
            {/* Active Filter */}
            <div className="flex gap-2">
              <button
                onClick={() => setFilterActive('all')}
                className={`px-4 py-2 text-sm rounded-md transition-colors ${
                  filterActive === 'all' 
                    ? 'bg-primary text-white' 
                    : 'bg-gray-100 hover:bg-gray-200'
                }`}
              >
                All Users
              </button>
              <button
                onClick={() => setFilterActive('active')}
                className={`px-4 py-2 text-sm rounded-md transition-colors ${
                  filterActive === 'active' 
                    ? 'bg-green-500 text-white' 
                    : 'bg-gray-100 hover:bg-gray-200'
                }`}
              >
                🟢 Active
              </button>
              <button
                onClick={() => setFilterActive('inactive')}
                className={`px-4 py-2 text-sm rounded-md transition-colors ${
                  filterActive === 'inactive' 
                    ? 'bg-red-500 text-white' 
                    : 'bg-gray-100 hover:bg-gray-200'
                }`}
              >
                🔴 Inactive
              </button>
            </div>

            {/* Group Filter */}
            <select
              value={filterGroup || ''}
              onChange={(e) => setFilterGroup(e.target.value ? Number(e.target.value) : null)}
              className="px-3 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">All Groups</option>
              {groups.filter(g => g.is_active).map(g => (
                <option key={g.id} value={g.id}>{g.name}</option>
              ))}
            </select>

            <div className="flex-1 text-right text-sm text-muted-foreground">
              {filteredUsers.length} user{filteredUsers.length !== 1 ? 's' : ''}
            </div>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-md text-destructive">
            {error}
          </div>
        )}

        {/* User Cards */}
        <div className="space-y-3">
          {filteredUsers.map(user => (
            <div
              key={user.id}
              onDragOver={(e) => handleDragOver(e, user.id)}
              onDragLeave={handleDragLeave}
              onDrop={() => handleDrop(user)}
              className={`bg-white p-6 rounded-lg border-2 transition-all duration-200 ${
                dragOverUser === user.id
                  ? 'border-primary bg-primary/5 shadow-lg scale-[1.02]'
                  : 'border-gray-200 hover:border-gray-300 hover:shadow-md'
              }`}
            >
              {/* User Header */}
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-semibold text-gray-900">{user.full_name}</h3>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      user.is_active 
                        ? 'bg-green-100 text-green-700' 
                        : 'bg-red-100 text-red-700'
                    }`}>
                      {user.is_active ? '🟢 Active' : '🔴 Inactive'}
                    </span>
                    {user.is_qms_admin && (
                      <span className="px-2 py-1 text-xs font-semibold bg-purple-100 text-purple-700 rounded-full">
                        👑 QMS Admin
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-muted-foreground mt-1">{user.email}</div>
                  {user.employee_id && (
                    <div className="text-xs text-muted-foreground">ID: {user.employee_id}</div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <button 
                    onClick={() => {
                      setSelectedUser(user)
                      setShowEditUserModal(true)
                    }}
                    className="px-3 py-1.5 text-sm border border-gray-300 rounded-md hover:bg-primary hover:text-white hover:border-primary transition-all"
                  >
                    ✏️ Edit
                  </button>
                  {!user.cannot_be_deleted && (
                    user.is_active ? (
                      <button 
                        onClick={() => handleDeactivateUser(user.id)}
                        className="px-3 py-1.5 text-sm border border-red-300 text-red-600 rounded-md hover:bg-red-50 transition-all"
                      >
                        ⏸️ Deactivate
                      </button>
                    ) : (
                      <button 
                        onClick={() => handleReactivateUser(user.id)}
                        className="px-3 py-1.5 text-sm border border-green-300 text-green-600 rounded-md hover:bg-green-50 transition-all"
                      >
                        ▶️ Reactivate
                      </button>
                    )
                  )}
                </div>
              </div>

              {/* Interest Group Badges */}
              <div>
                <div className="text-xs font-medium text-gray-600 mb-2">Interest Groups:</div>
                {user.memberships.length > 0 ? (
                  <div className="flex gap-2 flex-wrap">
                    {user.memberships.map(membership => {
                      const group = groups.find(g => g.id === membership.interest_group_id)
                      if (!group) return null
                      const level = membership.approval_level as keyof typeof LEVEL_COLORS
                      
                      return (
                        <button
                          key={membership.id}
                          onClick={() => handleBadgeClick(user, membership)}
                          className={`px-3 py-1.5 text-sm font-medium rounded-md border-2 transition-all ${LEVEL_COLORS[level]}`}
                          title={`${group.name} - Level ${level} (${LEVEL_NAMES[level]})\nClick to edit`}
                        >
                          <span className="font-bold mr-1">L{level}</span>
                          {group.code}
                        </button>
                      )
                    })}
                  </div>
                ) : (
                  <div className="text-sm text-muted-foreground italic border-2 border-dashed border-gray-200 rounded-md p-3 text-center">
                    {dragOverUser === user.id 
                      ? '👆 Drop group here to assign' 
                      : 'No groups assigned yet - drag groups here'}
                  </div>
                )}
              </div>
            </div>
          ))}

          {filteredUsers.length === 0 && (
            <div className="text-center py-12 text-muted-foreground">
              <div className="text-4xl mb-2">🔍</div>
              <div>No users found</div>
            </div>
          )}
        </div>
      </div>

        {/* RIGHT: Interest Groups Sidebar (40%) */}
        <div className="w-[28rem] space-y-4">
          {/* Search & Filter */}
          <div className="bg-white p-4 rounded-lg border border-gray-200 space-y-4">
            <div className="flex gap-4">
              <input
                type="text"
                placeholder="🔍 Search groups..."
                value={groupSearchQuery}
                onChange={(e) => setGroupSearchQuery(e.target.value)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <button 
                onClick={() => setShowCreateGroupModal(true)}
                className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90 transition-colors"
              >
                ➕ New
              </button>
            </div>

            <div className="flex gap-4 flex-wrap">
              {/* Active Filter */}
              <div className="flex gap-2">
                <button
                  onClick={() => setGroupFilterActive('all')}
                  className={`px-4 py-2 text-sm rounded-md transition-colors ${
                    groupFilterActive === 'all' 
                      ? 'bg-primary text-white' 
                      : 'bg-gray-100 hover:bg-gray-200'
                  }`}
                >
                  All Groups
                </button>
                <button
                  onClick={() => setGroupFilterActive('active')}
                  className={`px-4 py-2 text-sm rounded-md transition-colors ${
                    groupFilterActive === 'active' 
                      ? 'bg-green-500 text-white' 
                      : 'bg-gray-100 hover:bg-gray-200'
                  }`}
                >
                  🟢 Active
                </button>
                <button
                  onClick={() => setGroupFilterActive('inactive')}
                  className={`px-4 py-2 text-sm rounded-md transition-colors ${
                    groupFilterActive === 'inactive' 
                      ? 'bg-red-500 text-white' 
                      : 'bg-gray-100 hover:bg-gray-200'
                  }`}
                >
                  🔴 Inactive
                </button>
              </div>

              <div className="flex-1 text-right text-sm text-muted-foreground">
                {filteredGroups.length} group{filteredGroups.length !== 1 ? 's' : ''}
              </div>
            </div>
          </div>

          {/* Groups List */}
          <div className="bg-white p-4 rounded-lg border border-gray-200 sticky top-4">
            <div className="text-xs text-muted-foreground mb-3">
              💡 Drag groups onto users to assign
            </div>

          <div className="space-y-2">
            {filteredGroups.map(group => (
              <div
                key={group.id}
                draggable={group.is_active}
                onDragStart={() => group.is_active && handleDragStart(group)}
                className={`group p-3 rounded-md border border-gray-200 transition-all ${
                  group.is_active 
                    ? 'bg-gray-50 cursor-move hover:bg-primary hover:text-white hover:border-primary' 
                    : 'bg-gray-100 cursor-not-allowed opacity-60'
                }`}
              >
                <div className="flex justify-between items-center">
                  <div className="flex-1">
                    <div className="font-semibold text-sm">{group.code}</div>
                    <div className="text-xs opacity-70">{group.name}</div>
                    {!group.is_active && (
                      <div className="text-xs text-red-600 font-medium">⚠️ Inaktiv</div>
                    )}
                  </div>
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-all">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedGroup(group)
                        setEditGroup({
                          name: group.name,
                          code: group.code,
                          description: group.description || '',
                          is_external: group.is_external,
                          is_active: group.is_active,
                        })
                        setShowEditGroupModal(true)
                      }}
                      className="px-2 py-1 text-xs bg-white text-gray-700 rounded hover:bg-gray-100 transition-all"
                    >
                      ✏️
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleToggleGroupActive(group.id, group.name, group.is_active)
                      }}
                      className={`px-2 py-1 text-xs rounded transition-all ${
                        group.is_active
                          ? 'bg-white text-red-600 hover:bg-red-50'
                          : 'bg-white text-green-600 hover:bg-green-50'
                      }`}
                    >
                      {group.is_active ? '⏸️' : '▶️'}
                    </button>
                  </div>
                </div>
              </div>
            ))}
            
            {filteredGroups.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                <div className="text-2xl mb-2">🔍</div>
                <div className="text-sm">No groups found</div>
              </div>
            )}
          </div>

            {/* Legend */}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="text-xs font-medium text-gray-600 mb-2">Levels:</div>
              <div className="space-y-1">
                {Object.entries(LEVEL_NAMES).map(([level, name]) => (
                  <div key={level} className="flex items-center gap-2 text-xs">
                    <div className={`w-3 h-3 rounded border ${LEVEL_COLORS[Number(level) as keyof typeof LEVEL_COLORS]}`} />
                    <span>L{level} - {name}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Level Selection Modal */}
      {showLevelModal && selectedUser && selectedGroup && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold mb-4">
              {selectedMembership ? 'Edit' : 'Assign'} Membership
            </h3>

            <div className="mb-4">
              <div className="text-sm text-muted-foreground mb-2">
                User: <span className="font-semibold text-foreground">{selectedUser.full_name}</span>
              </div>
              <div className="text-sm text-muted-foreground mb-4">
                Group: <span className="font-semibold text-foreground">{selectedGroup.name}</span>
              </div>

              <label className="block text-sm font-medium mb-2">Permission Level:</label>
              <select
                value={selectedLevel}
                onChange={(e) => setSelectedLevel(Number(e.target.value))}
                className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value={1}>Level 1 - Mitarbeiter</option>
                <option value={2}>Level 2 - Teamleiter</option>
                <option value={3}>Level 3 - Abteilungsleiter</option>
                <option value={4}>Level 4 - QM-Manager</option>
              </select>

              <div className={`mt-3 p-3 rounded-md border-2 ${LEVEL_COLORS[selectedLevel as keyof typeof LEVEL_COLORS]}`}>
                <div className="font-semibold">Preview:</div>
                <div className="text-sm">Level {selectedLevel} - {LEVEL_NAMES[selectedLevel as keyof typeof LEVEL_NAMES]}</div>
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleSaveMembership}
                className="flex-1 px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90 transition-colors"
              >
                {selectedMembership ? 'Update' : 'Assign'}
              </button>
              
              {selectedMembership && (
                <button
                  onClick={handleRemoveMembership}
                  className="px-4 py-2 bg-destructive text-white rounded-md hover:bg-destructive/90 transition-colors"
                >
                  Remove
                </button>
              )}
              
              <button
                onClick={() => {
                  setShowLevelModal(false)
                  setSelectedUser(null)
                  setSelectedGroup(null)
                  setSelectedMembership(null)
                }}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {showEditUserModal && selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-bold mb-4">Edit User</h3>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Full Name *</label>
                  <input
                    type="text"
                    value={selectedUser.full_name}
                    onChange={(e) => setSelectedUser({...selectedUser, full_name: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Email *</label>
                  <input
                    type="email"
                    value={selectedUser.email}
                    onChange={(e) => setSelectedUser({...selectedUser, email: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Employee ID</label>
                  <input
                    type="text"
                    value={selectedUser.employee_id || ''}
                    onChange={(e) => setSelectedUser({...selectedUser, employee_id: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Organizational Unit</label>
                  <input
                    type="text"
                    value={selectedUser.organizational_unit || ''}
                    onChange={(e) => setSelectedUser({...selectedUser, organizational_unit: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
              </div>

              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={selectedUser.is_active}
                    onChange={(e) => setSelectedUser({...selectedUser, is_active: e.target.checked})}
                    className="w-4 h-4"
                  />
                  <span className="text-sm font-medium">Active</span>
                </label>
              </div>

              {selectedUser.is_qms_admin && (
                <div className="p-3 bg-purple-50 border border-purple-200 rounded-md text-sm text-purple-700">
                  👑 This user is a QMS Admin (Level 5) and cannot be deleted
                </div>
              )}
            </div>

            <div className="flex gap-2 mt-6">
              <button
                onClick={async () => {
                  try {
                    const response = await usersApi.update(selectedUser.id, {
                      full_name: selectedUser.full_name,
                      email: selectedUser.email,
                      employee_id: selectedUser.employee_id,
                      organizational_unit: selectedUser.organizational_unit,
                      is_active: selectedUser.is_active,
                    })
                    
                    if (response.data) {
                      await loadData()
                      setShowEditUserModal(false)
                      setSelectedUser(null)
                      setError('')
                    } else {
                      setError(response.error || 'Failed to update user')
                    }
                  } catch (err) {
                    setError('Failed to update user')
                  }
                }}
                className="flex-1 px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90 transition-colors"
              >
                Save Changes
              </button>
              
              <button
                onClick={() => {
                  setShowEditUserModal(false)
                  setSelectedUser(null)
                }}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create User Modal */}
      {showCreateUserModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-bold mb-4">Create New User</h3>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Full Name *</label>
                  <input
                    type="text"
                    value={newUser.full_name}
                    onChange={(e) => setNewUser({...newUser, full_name: e.target.value})}
                    placeholder="Max Mustermann"
                    className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Email *</label>
                  <input
                    type="email"
                    value={newUser.email}
                    onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                    placeholder="max.mustermann@company.com"
                    className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Password *</label>
                  <input
                    type="password"
                    value={newUser.password}
                    onChange={(e) => setNewUser({...newUser, password: e.target.value})}
                    placeholder="Min. 8 characters"
                    className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Employee ID</label>
                  <input
                    type="text"
                    value={newUser.employee_id}
                    onChange={(e) => setNewUser({...newUser, employee_id: e.target.value})}
                    placeholder="EMP-001"
                    className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium mb-1">Organizational Unit</label>
                  <input
                    type="text"
                    value={newUser.organizational_unit}
                    onChange={(e) => setNewUser({...newUser, organizational_unit: e.target.value})}
                    placeholder="z.B. Produktion, Service, Einkauf"
                    className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
              </div>

              <div className="p-3 bg-blue-50 border border-blue-200 rounded-md text-sm text-blue-700">
                💡 After creating the user, you can drag interest groups onto them to assign permissions
              </div>
            </div>

            <div className="flex gap-2 mt-6">
              <button
                onClick={async () => {
                  try {
                    if (!newUser.email || !newUser.full_name || !newUser.password) {
                      setError('Please fill in all required fields')
                      return
                    }

                    if (newUser.password.length < 8) {
                      setError('Password must be at least 8 characters')
                      return
                    }

                    const response = await usersApi.create({
                      email: newUser.email,
                      full_name: newUser.full_name,
                      password: newUser.password,
                      employee_id: newUser.employee_id || undefined,
                      organizational_unit: newUser.organizational_unit || undefined,
                    })
                    
                    if (response.data) {
                      await loadData()
                      setShowCreateUserModal(false)
                      setNewUser({
                        email: '',
                        full_name: '',
                        password: '',
                        employee_id: '',
                        organizational_unit: '',
                      })
                      setError('')
                    } else {
                      setError(response.error || 'Failed to create user')
                    }
                  } catch (err) {
                    setError('Failed to create user')
                  }
                }}
                className="flex-1 px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90 transition-colors"
              >
                Create User
              </button>
              
              <button
                onClick={() => {
                  setShowCreateUserModal(false)
                  setNewUser({
                    email: '',
                    full_name: '',
                    password: '',
                    employee_id: '',
                    organizational_unit: '',
                  })
                }}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Group Modal */}
      {showCreateGroupModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold mb-4">Create Interest Group</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Name *</label>
                <input
                  type="text"
                  value={newGroup.name}
                  onChange={(e) => setNewGroup({...newGroup, name: e.target.value})}
                  placeholder="z.B. Qualitätsmanagement"
                  className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Code *</label>
                <input
                  type="text"
                  value={newGroup.code}
                  onChange={(e) => setNewGroup({...newGroup, code: e.target.value})}
                  placeholder="z.B. qm, service, einkauf"
                  className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  value={newGroup.description}
                  onChange={(e) => setNewGroup({...newGroup, description: e.target.value})}
                  placeholder="Beschreibung der Interest Group..."
                  rows={3}
                  className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_external"
                  checked={newGroup.is_external}
                  onChange={(e) => setNewGroup({...newGroup, is_external: e.target.checked})}
                  className="rounded"
                />
                <label htmlFor="is_external" className="text-sm">External Group (z.B. Lieferanten, Kunden)</label>
              </div>
            </div>

            <div className="flex gap-2 mt-6">
              <button
                onClick={handleCreateGroup}
                className="flex-1 px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90 transition-colors"
              >
                Create Group
              </button>
              
              <button
                onClick={() => {
                  setShowCreateGroupModal(false)
                  setNewGroup({
                    name: '',
                    code: '',
                    description: '',
                    is_external: false,
                  })
                }}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Group Modal */}
      {showEditGroupModal && selectedGroup && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold mb-4">Edit Interest Group</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Name *</label>
                <input
                  type="text"
                  value={editGroup.name}
                  onChange={(e) => setEditGroup({...editGroup, name: e.target.value})}
                  placeholder="z.B. Qualitätsmanagement"
                  className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Code *</label>
                <input
                  type="text"
                  value={editGroup.code}
                  onChange={(e) => setEditGroup({...editGroup, code: e.target.value})}
                  placeholder="z.B. qm, service, einkauf"
                  className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  value={editGroup.description}
                  onChange={(e) => setEditGroup({...editGroup, description: e.target.value})}
                  placeholder="Beschreibung der Interest Group..."
                  rows={3}
                  className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="edit_is_external"
                  checked={editGroup.is_external}
                  onChange={(e) => setEditGroup({...editGroup, is_external: e.target.checked})}
                  className="rounded"
                />
                <label htmlFor="edit_is_external" className="text-sm">External Group (z.B. Lieferanten, Kunden)</label>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="edit_is_active"
                  checked={editGroup.is_active}
                  onChange={(e) => setEditGroup({...editGroup, is_active: e.target.checked})}
                  className="rounded"
                />
                <label htmlFor="edit_is_active" className="text-sm">Active (Group is available for assignment)</label>
              </div>
            </div>

            <div className="flex gap-2 mt-6">
              <button
                onClick={handleEditGroup}
                className="flex-1 px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90 transition-colors"
              >
                Update Group
              </button>
              
              <button
                onClick={() => {
                  setShowEditGroupModal(false)
                  setSelectedGroup(null)
                }}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

