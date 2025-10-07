'use client'

import { useState, useEffect } from 'react'
import { interestGroupsApi } from '@/lib/api'

interface InterestGroup {
  id: number
  name: string
  code: string
  description: string
  is_active: boolean
  created_at: string
}

export default function InterestGroupsPage() {
  const [groups, setGroups] = useState<InterestGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchGroups()
  }, [])

  const fetchGroups = async () => {
    try {
      const response = await interestGroupsApi.list()
      
      if (response.data) {
        setGroups(response.data)
        setError('')
      } else {
        setError(response.error || 'Failed to fetch interest groups')
      }
    } catch (err) {
      setError('Network error')
    } finally {
      setLoading(false)
    }
  }

  const handleSoftDelete = async (id: number) => {
    try {
      const response = await interestGroupsApi.delete(id)
      
      if (response.data) {
        // Refresh the list
        fetchGroups()
        setError('')
      } else {
        setError(response.error || 'Failed to delete interest group')
      }
    } catch (err) {
      setError('Network error')
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">Loading interest groups...</div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-foreground">Interest Groups</h1>
        <button className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90">
          Create New Group
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-destructive/10 border border-destructive/20 rounded-md text-destructive">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {groups.map((group) => (
          <div key={group.id} className="bg-white border-2 border-gray-200 rounded-lg p-6 hover:border-primary hover:shadow-lg transition-all duration-300">
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-xl font-semibold">{group.name}</h2>
              <span className={`px-2 py-1 text-xs rounded-full ${
                group.is_active 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {group.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
            
            <div className="space-y-2 mb-4">
              <div>
                <span className="text-sm text-muted-foreground">Code:</span>
                <div className="font-mono text-sm">{group.code}</div>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">Description:</span>
                <div className="text-sm">{group.description}</div>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">Created:</span>
                <div className="text-sm">{new Date(group.created_at).toLocaleDateString()}</div>
              </div>
            </div>

            <div className="flex gap-2">
              <button className="px-3 py-1 text-sm border border-gray-300 text-gray-700 rounded-md hover:bg-primary hover:text-white hover:border-primary transition-all duration-300">
                Edit
              </button>
              {group.is_active && (
                <button 
                  onClick={() => handleSoftDelete(group.id)}
                  className="px-3 py-1 text-sm border border-destructive text-destructive rounded-md hover:bg-destructive/10"
                >
                  Delete
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
