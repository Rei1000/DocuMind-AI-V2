/**
 * Interest Groups API
 * 
 * API-Funktionen für Interest Groups Management
 */

export interface InterestGroup {
  id: number;
  name: string;
  code: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface InterestGroupResponse {
  success: boolean;
  data: InterestGroup[];
}

/**
 * Lade alle Interest Groups
 */
export async function getInterestGroups(): Promise<InterestGroup[]> {
  try {
    const response = await fetch('http://localhost:8000/api/interest-groups/', {
      headers: {
        'Authorization': `Bearer ${sessionStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    // Backend liefert direkt ein Array
    if (Array.isArray(data)) {
      return data;
    } else if (data.success && Array.isArray(data.data)) {
      return data.data;
    } else {
      console.error('Invalid interest groups response format:', data);
      return [];
    }
  } catch (error) {
    console.error('Failed to fetch interest groups:', error);
    return [];
  }
}

/**
 * Lade Interest Group by ID
 */
export async function getInterestGroupById(id: number): Promise<InterestGroup | null> {
  try {
    const response = await fetch(`http://localhost:8000/api/interest-groups/${id}`, {
      headers: {
        'Authorization': `Bearer ${sessionStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error(`Failed to fetch interest group ${id}:`, error);
    return null;
  }
}

/**
 * Erstelle Interest Group Name Lookup Map
 */
export function createInterestGroupLookup(groups: InterestGroup[]): Map<number, InterestGroup> {
  const lookup = new Map<number, InterestGroup>();
  groups.forEach(group => {
    lookup.set(group.id, group);
  });
  return lookup;
}

/**
 * Hole Interest Group Name by ID
 */
export function getInterestGroupName(lookup: Map<number, InterestGroup>, id: number): string {
  const group = lookup.get(id);
  return group ? group.name : `IG ${id}`;
}

/**
 * Hole Interest Group Code by ID
 */
export function getInterestGroupCode(lookup: Map<number, InterestGroup>, id: number): string {
  const group = lookup.get(id);
  return group ? group.code : `IG${id}`;
}
