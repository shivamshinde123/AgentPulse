import { useState, useEffect } from 'react'
import { apiClient } from '../api/client'

export function useSessions(filters) {
  const [sessions, setSessions] = useState([])
  const [totalCount, setTotalCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    const params = {}
    if (filters.language) params.language = filters.language
    if (filters.status && filters.status !== 'all') params.status = filters.status
    if (filters.startDate) params.start_date = filters.startDate
    if (filters.endDate) params.end_date = filters.endDate
    if (filters.limit) params.limit = filters.limit
    if (filters.offset) params.offset = filters.offset

    apiClient
      .get('/api/sessions', { params })
      .then((response) => {
        if (cancelled) return
        setSessions(response.data.sessions || [])
        setTotalCount(response.data.total_count || 0)
      })
      .catch((err) => {
        if (cancelled) return
        console.error('Error fetching sessions:', err)
        setError(err.message)
        setSessions([])
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [
    filters.language,
    filters.status,
    filters.startDate,
    filters.endDate,
    filters.limit,
    filters.offset,
  ])

  return { sessions, totalCount, loading, error }
}
