'use client'

import { useState, useEffect } from 'react'
import { usersApi, interestGroupsApi } from '@/lib/api'
import { User, InterestGroup, UserGroupMembership } from '@/types'

/**
 * 🎨 Matrix-View für User × Interest Groups
 * 
 * Features:
 * - Drag & Drop: Interest Group → User Cell
 * - Click auf Zelle: Level ändern/entfernen
 * - Farbcodierung: L1-L5
 * - Hover-Tooltips mit Details
 */

interface MatrixCellData {
  userId: number
  groupId: number
  membership?: UserGroupMembership
}

// Farbcodierung nach Level
const LEVEL_COLORS = {
  1: 'bg-gray-100 text-gray-700 border-gray-300',      // Mitarbeiter
  2: 'bg-blue-100 text-blue-700 border-blue-300',      // Teamleiter
  3: 'bg-orange-100 text-orange-700 border-orange-300', // Abteilungsleiter
  4: 'bg-green-100 text-green-700 border-green-300',   // QM-Manager
  5: 'bg-purple-100 text-purple-700 border-purple-300' // QMS Admin (nur qms.admin)
}

const LEVEL_NAMES = {
  1: 'Mitarbeiter',
  2: 'Teamleiter',
  3: 'Abteilungsleiter',
  4: 'QM-Manager',
  5: 'QMS Admin'
}

export default function UserMatrixView() {
  const [users, setUsers] = useState<User[]>([])
  const [groups, setGroups] = useState<InterestGroup[]>([])
  const [memberships, setMemberships] = useState<Map<string, UserGroupMembership>>(new Map())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  
  // Modal State
  const [showModal, setShowModal] = useState(false)
  const [selectedCell, setSelectedCell] = useState<MatrixCellData | null>(null)
  const [selectedLevel, setSelectedLevel] = useState<number>(1)
  
  // Drag State
  const [draggedGroup, setDraggedGroup] = useState<InterestGroup | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      // Load Users
      const usersResp = await usersApi.list()
      if (usersResp.data) {
        setUsers(usersResp.data)
      }

      // Load Interest Groups
      const groupsResp = await interestGroupsApi.list()
      if (groupsResp.data) {
        setGroups(groupsResp.data)
      }

      // Load all memberships for all users
      if (usersResp.data) {
        const membershipMap = new Map<string, UserGroupMembership>()
        
        for (const user of usersResp.data) {
          const membershipResp = await usersApi.getMemberships(user.id)
          if (membershipResp.data) {
            membershipResp.data.forEach((m: UserGroupMembership) => {
              const key = `${m.user_id}-${m.interest_group_id}`
              membershipMap.set(key, m)
            })
          }
        }
        
        setMemberships(membershipMap)
      }

      setError('')
    } catch (err) {
      setError('Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const getMembership = (userId: number, groupId: number): UserGroupMembership | undefined => {
    return memberships.get(`${userId}-${groupId}`)
  }

  const handleCellClick = (userId: number, groupId: number) => {
    const membership = getMembership(userId, groupId)
    setSelectedCell({ userId, groupId, membership })
    setSelectedLevel(membership?.approval_level || 1)
    setShowModal(true)
  }

  const handleSaveMembership = async () => {
    if (!selectedCell) return

    try {
      const { userId, groupId, membership } = selectedCell

      if (membership) {
        // Update existing membership (via remove + add, da kein update endpoint existiert)
        await usersApi.removeMembership(userId, groupId)
      }

      // Add new membership
      await usersApi.addMembership(userId, {
        interest_group_id: groupId,
        approval_level: selectedLevel,
        role_in_group: LEVEL_NAMES[selectedLevel as keyof typeof LEVEL_NAMES],
        is_department_head: selectedLevel >= 3,
      })

      // Reload data
      await loadData()
      setShowModal(false)
      setSelectedCell(null)
    } catch (err) {
      setError('Failed to save membership')
    }
  }

  const handleRemoveMembership = async () => {
    if (!selectedCell?.membership) return

    try {
      await usersApi.removeMembership(selectedCell.userId, selectedCell.groupId)
      await loadData()
      setShowModal(false)
      setSelectedCell(null)
    } catch (err) {
      setError('Failed to remove membership')
    }
  }

  // Drag & Drop Handlers
  const handleDragStart = (group: InterestGroup) => {
    setDraggedGroup(group)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const handleDrop = async (userId: number) => {
    if (!draggedGroup) return

    // Open modal for level selection
    const membership = getMembership(userId, draggedGroup.id)
    setSelectedCell({ userId, groupId: draggedGroup.id, membership })
    setSelectedLevel(membership?.approval_level || 1)
    setShowModal(true)
    setDraggedGroup(null)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="text-lg font-semibold mb-2">Loading Matrix...</div>
          <div className="text-sm text-muted-foreground">Fetching users and groups...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-foreground">User × Interest Groups Matrix</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Drag groups onto users to assign them, or click cells to edit levels
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-md text-destructive">
          {error}
        </div>
      )}

      {/* Legend */}
      <div className="flex gap-4 flex-wrap p-4 bg-gray-50 rounded-lg border border-gray-200">
        <div className="font-semibold text-sm">Level:</div>
        {Object.entries(LEVEL_NAMES).map(([level, name]) => (
          <div key={level} className="flex items-center gap-2">
            <div className={`w-4 h-4 rounded border ${LEVEL_COLORS[Number(level) as keyof typeof LEVEL_COLORS]}`} />
            <span className="text-sm">L{level} - {name}</span>
          </div>
        ))}
      </div>

      {/* Draggable Interest Groups */}
      <div className="p-4 bg-white rounded-lg border-2 border-dashed border-gray-300">
        <div className="font-semibold text-sm mb-3 text-gray-700">📌 Drag these groups onto users:</div>
        <div className="flex gap-2 flex-wrap">
          {groups.map((group) => (
            <div
              key={group.id}
              draggable
              onDragStart={() => handleDragStart(group)}
              className="px-4 py-2 bg-primary text-white rounded-md cursor-move hover:bg-primary/90 transition-all duration-200 shadow-sm hover:shadow-md"
            >
              <span className="font-semibold">{group.code}</span>
              <span className="ml-2 text-sm opacity-90">{group.name}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Matrix Table */}
      <div className="overflow-x-auto border rounded-lg">
        <table className="w-full border-collapse bg-white">
          <thead>
            <tr className="bg-gray-50 border-b-2 border-gray-200">
              <th className="p-4 text-left font-semibold text-gray-700 sticky left-0 bg-gray-50 border-r-2 border-gray-200">
                User
              </th>
              {groups.map((group) => (
                <th key={group.id} className="p-4 text-center font-semibold text-gray-700 min-w-[100px]">
                  <div className="text-sm">{group.code}</div>
                  <div className="text-xs font-normal text-muted-foreground">{group.name}</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id} className="border-b border-gray-200 hover:bg-gray-50">
                <td className="p-4 sticky left-0 bg-white border-r-2 border-gray-200">
                  <div className="font-medium text-gray-900">{user.full_name}</div>
                  <div className="text-xs text-muted-foreground">{user.email}</div>
                  {user.is_qms_admin && (
                    <div className="text-xs font-semibold text-purple-600 mt-1">🟣 QMS Admin (L5)</div>
                  )}
                </td>
                {groups.map((group) => {
                  const membership = getMembership(user.id, group.id)
                  const level = membership?.approval_level
                  const isQmsAdmin = user.is_qms_admin

                  return (
                    <td
                      key={group.id}
                      className="p-2 text-center border-r border-gray-100"
                      onDragOver={handleDragOver}
                      onDrop={() => handleDrop(user.id)}
                    >
                      {membership || isQmsAdmin ? (
                        <button
                          onClick={() => handleCellClick(user.id, group.id)}
                          className={`w-full px-3 py-2 rounded border-2 transition-all duration-200 hover:scale-105 hover:shadow-md ${
                            LEVEL_COLORS[(level || 5) as keyof typeof LEVEL_COLORS]
                          }`}
                          title={`${LEVEL_NAMES[(level || 5) as keyof typeof LEVEL_NAMES]} - Click to edit`}
                        >
                          <div className="font-bold">L{level || 5}</div>
                          {membership?.role_in_group && (
                            <div className="text-xs mt-1">{membership.role_in_group}</div>
                          )}
                        </button>
                      ) : (
                        <button
                          onClick={() => handleCellClick(user.id, group.id)}
                          className="w-full px-3 py-6 rounded border-2 border-dashed border-gray-200 hover:border-primary hover:bg-primary/5 transition-all duration-200"
                          title="Click or drop group here to assign"
                        >
                          <span className="text-gray-400 text-2xl">+</span>
                        </button>
                      )}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Level Selection Modal */}
      {showModal && selectedCell && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold mb-4">
              {selectedCell.membership ? 'Edit' : 'Assign'} Membership
            </h3>

            <div className="mb-4">
              <div className="text-sm text-muted-foreground mb-2">
                User: <span className="font-semibold text-foreground">
                  {users.find(u => u.id === selectedCell.userId)?.full_name}
                </span>
              </div>
              <div className="text-sm text-muted-foreground mb-4">
                Group: <span className="font-semibold text-foreground">
                  {groups.find(g => g.id === selectedCell.groupId)?.name}
                </span>
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
                {selectedCell.membership ? 'Update' : 'Assign'}
              </button>
              
              {selectedCell.membership && (
                <button
                  onClick={handleRemoveMembership}
                  className="px-4 py-2 bg-destructive text-white rounded-md hover:bg-destructive/90 transition-colors"
                >
                  Remove
                </button>
              )}
              
              <button
                onClick={() => {
                  setShowModal(false)
                  setSelectedCell(null)
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

