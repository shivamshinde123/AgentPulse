import { useState, useMemo } from 'react'
import { BarChart3, MessageSquare, ThumbsUp, Code } from 'lucide-react'
import LanguageFilter from '../components/Filters/LanguageFilter'
import Timeline from '../components/Charts/Timeline'
import ErrorDistribution from '../components/Charts/ErrorDistribution'
import ScatterPlot from '../components/Charts/ScatterPlot'
import InsightsPanel from '../components/InsightsPanel'
import { useSessions } from '../hooks/useSessions'
import { useMetrics } from '../hooks/useMetrics'

function Dashboard() {
  const [filters, setFilters] = useState({
    language: null,
  })

  const { sessions, loading: sessionsLoading, error: sessionsError } = useSessions(filters)
  const { metrics, loading: metricsLoading, error: metricsError } = useMetrics(filters)
  const handleLanguageChange = (language) => {
    setFilters((prev) => ({ ...prev, language }))
  }

  const kpis = useMemo(() => {
    if (!sessions || sessions.length === 0) {
      return {
        totalSessions: 0,
        totalInteractions: 0,
        avgAcceptanceRate: '0.0',
        topLanguage: 'N/A',
      }
    }

    const langCounts = sessions.reduce((acc, s) => {
      acc[s.language] = (acc[s.language] || 0) + 1
      return acc
    }, {})
    const topLang = Object.entries(langCounts).sort((a, b) => b[1] - a[1])

    const ratesWithValues = sessions.filter((s) => s.acceptance_rate != null)
    const avgRate =
      ratesWithValues.length > 0
        ? ratesWithValues.reduce((sum, s) => sum + s.acceptance_rate, 0) / ratesWithValues.length
        : 0

    return {
      totalSessions: sessions.length,
      totalInteractions: sessions.reduce((sum, s) => sum + (s.interaction_count || 0), 0),
      avgAcceptanceRate: (avgRate * 100).toFixed(1),
      topLanguage: topLang.length > 0 ? topLang[0][0] : 'N/A',
    }
  }, [sessions])

  const loading = sessionsLoading || metricsLoading
  const fetchError = sessionsError || metricsError

  return (
    <div className="dashboard">
      {/* KPI Cards */}
      <div className="kpi-cards">
        <div className="kpi-card">
          <div className="kpi-icon">
            <BarChart3 size={24} />
          </div>
          <div className="kpi-info">
            <span className="kpi-label">Total Sessions</span>
            <span className="kpi-value">{loading ? '-' : kpis.totalSessions}</span>
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon">
            <MessageSquare size={24} />
          </div>
          <div className="kpi-info">
            <span className="kpi-label">Total Interactions</span>
            <span className="kpi-value">{loading ? '-' : kpis.totalInteractions}</span>
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon">
            <ThumbsUp size={24} />
          </div>
          <div className="kpi-info">
            <span className="kpi-label">Avg Acceptance Rate</span>
            <span className="kpi-value">{loading ? '-' : `${kpis.avgAcceptanceRate}%`}</span>
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon">
            <Code size={24} />
          </div>
          <div className="kpi-info">
            <span className="kpi-label">Top Language</span>
            <span className="kpi-value">{loading ? '-' : kpis.topLanguage}</span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="filters-panel">
        <h3>Filters</h3>
        <div className="filters-row">
          <LanguageFilter onLanguageChange={handleLanguageChange} />
        </div>
      </div>

      {fetchError && (
        <div className="error-state" role="alert">
          Error loading data: {fetchError}
        </div>
      )}

      {loading ? (
        <div className="loading-state">Loading dashboard data...</div>
      ) : (
        <>
          {/* Charts */}
          <div className="charts-grid">
            <div className="chart-card">
              <h3>Acceptance Rate Over Time</h3>
              <div className="chart-body">
                <Timeline
                  data={metrics?.acceptanceTrend || []}
                  title=""
                  yLabel="Acceptance Rate"
                />
              </div>
            </div>

            <div className="chart-card">
              <h3>Error Distribution</h3>
              <div className="chart-body">
                <ErrorDistribution data={metrics?.errorDistribution || {}} title="" />
              </div>
            </div>

            <div className="chart-card chart-card-wide">
              <h3>Duration vs Interactions</h3>
              <div className="chart-body">
                <ScatterPlot
                  data={sessions}
                  xKey="duration_seconds"
                  yKey="interaction_count"
                  sizeKey="error_count"
                  title=""
                />
              </div>
            </div>
          </div>

          {/* Insights */}
          <InsightsPanel metrics={metrics} sessions={sessions} />
        </>
      )}
    </div>
  )
}

export default Dashboard
