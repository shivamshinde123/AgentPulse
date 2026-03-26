# Frontend Service (React)

## Overview

The frontend dashboard visualizes analytics from the backend API. It displays interactive charts, filters, and insights about Claude Code sessions.

**Location**: `frontend/` directory  
**Language**: JavaScript/JSX  
**Framework**: React 18  
**Build Tool**: Vite  
**Port**: 5173 (localhost:5173)  
**Chart Library**: Plotly.js  
**HTTP Client**: Axios

## Responsibilities

1. **Fetch data** from backend APIs
2. **Display charts** (timeline, heatmap, scatter, bar)
3. **Enable filtering** (date range, language, status)
4. **Show KPIs** (acceptance rate, total sessions, error stats)
5. **Display insights** (auto-generated recommendations)

## Architecture

```
src/
├── main.jsx          (Entry point)
├── App.jsx           (Router, layout)
├── pages/
│   ├── Dashboard.jsx (Main dashboard with charts & filters)
│   ├── Sessions.jsx  (List all sessions)
│   └── SessionDetail.jsx (Optional: single session view)
├── components/
│   ├── Charts/
│   │   ├── Timeline.jsx
│   │   ├── Heatmap.jsx
│   │   └── ScatterPlot.jsx
│   ├── Filters/
│   │   ├── DateRange.jsx
│   │   └── LanguageFilter.jsx
│   └── InsightsPanel.jsx
├── hooks/
│   ├── useSessions.js
│   └── useMetrics.js
├── api/
│   └── client.js
└── styles/
    └── globals.css
```

## Dependencies (package.json)

```json
{
  "name": "claude-code-analyzer-frontend",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0",
    "plotly.js": "^2.26.0",
    "react-plotly.js": "^2.15.0",
    "date-fns": "^2.30.0",
    "lucide-react": "^0.263.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.0",
    "vite": "^4.4.0"
  }
}
```

## Module Details

### 1. main.jsx - Entry Point

```javascript
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles/globals.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

---

### 2. App.jsx - Router & Layout

```javascript
import React, { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Sessions from './pages/Sessions'
import './App.css'

function App() {
  return (
    <Router>
      <div className="app">
        {/* Navigation */}
        <nav className="navbar">
          <div className="container">
            <h1 className="logo">Claude Code Analyzer</h1>
            <ul className="nav-links">
              <li><Link to="/">Dashboard</Link></li>
              <li><Link to="/sessions">Sessions</Link></li>
            </ul>
          </div>
        </nav>

        {/* Main content */}
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/sessions" element={<Sessions />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
```

---

### 3. pages/Dashboard.jsx - Main Dashboard

```javascript
import React, { useState, useEffect } from 'react'
import DateRange from '../components/Filters/DateRange'
import LanguageFilter from '../components/Filters/LanguageFilter'
import Timeline from '../components/Charts/Timeline'
import Heatmap from '../components/Charts/Heatmap'
import ScatterPlot from '../components/Charts/ScatterPlot'
import InsightsPanel from '../components/InsightsPanel'
import { useSessions } from '../hooks/useSessions'
import { useMetrics } from '../hooks/useMetrics'
import '../styles/Dashboard.css'

function Dashboard() {
  const [filters, setFilters] = useState({
    language: null,
    status: 'all',
    startDate: null,
    endDate: null,
  })

  const { sessions, loading: sessionsLoading } = useSessions(filters)
  const { metrics, loading: metricsLoading } = useMetrics(filters)

  const handleDateChange = (startDate, endDate) => {
    setFilters(prev => ({ ...prev, startDate, endDate }))
  }

  const handleLanguageChange = (language) => {
    setFilters(prev => ({ ...prev, language }))
  }

  const handleStatusChange = (status) => {
    setFilters(prev => ({ ...prev, status }))
  }

  // KPI cards
  const kpis = {
    totalSessions: sessions.length,
    totalInteractions: sessions.reduce((sum, s) => sum + (s.interaction_count || 0), 0),
    avgAcceptanceRate: sessions.length > 0
      ? (sessions.reduce((sum, s) => sum + (s.acceptance_rate || 0), 0) / sessions.length * 100).toFixed(1)
      : 0,
    topLanguage: sessions.length > 0
      ? Object.entries(sessions.reduce((acc, s) => {
          acc[s.language] = (acc[s.language] || 0) + 1
          return acc
        }, {})).sort((a, b) => b[1] - a[1])[0][0]
      : 'N/A',
  }

  if (sessionsLoading || metricsLoading) {
    return <div className="dashboard loading">Loading...</div>
  }

  return (
    <div className="dashboard">
      {/* KPI Cards */}
      <div className="kpi-cards">
        <div className="kpi-card">
          <h3>Total Sessions</h3>
          <p className="kpi-value">{kpis.totalSessions}</p>
        </div>
        <div className="kpi-card">
          <h3>Total Interactions</h3>
          <p className="kpi-value">{kpis.totalInteractions}</p>
        </div>
        <div className="kpi-card">
          <h3>Avg Acceptance Rate</h3>
          <p className="kpi-value">{kpis.avgAcceptanceRate}%</p>
        </div>
        <div className="kpi-card">
          <h3>Top Language</h3>
          <p className="kpi-value">{kpis.topLanguage}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="filters-panel">
        <h3>Filters</h3>
        <div className="filter-group">
          <DateRange onDateChange={handleDateChange} />
        </div>
        <div className="filter-group">
          <LanguageFilter onLanguageChange={handleLanguageChange} />
        </div>
        <div className="filter-group">
          <label>Status</label>
          <select onChange={(e) => handleStatusChange(e.target.value)}>
            <option value="all">All</option>
            <option value="completed">Completed</option>
            <option value="abandoned">Abandoned</option>
            <option value="in_progress">In Progress</option>
          </select>
        </div>
      </div>

      {/* Charts */}
      <div className="charts-container">
        <div className="chart-card">
          <h3>Acceptance Rate Over Time</h3>
          <Timeline
            data={metrics?.acceptanceTrend || []}
            title="Acceptance Rate Timeline"
            yLabel="Acceptance Rate (%)"
          />
        </div>

        <div className="chart-card">
          <h3>Error Distribution</h3>
          <Heatmap
            data={metrics?.errorHeatmap || []}
            title="Error Types by Session Phase"
          />
        </div>

        <div className="chart-card">
          <h3>Session Metrics</h3>
          <ScatterPlot
            data={sessions}
            xKey="duration_seconds"
            yKey="interaction_count"
            sizeKey="error_count"
            title="Duration vs Interactions"
          />
        </div>
      </div>

      {/* Insights */}
      <InsightsPanel metrics={metrics} sessions={sessions} />
    </div>
  )
}

export default Dashboard
```

---

### 4. pages/Sessions.jsx - Session List

```javascript
import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { useSessions } from '../hooks/useSessions'
import '../styles/Sessions.css'

function Sessions() {
  const [sortBy, setSortBy] = useState('start_time')
  const [sortOrder, setSortOrder] = useState('desc')
  const [filters] = useState({})

  const { sessions, loading } = useSessions(filters)

  const handleSort = (column) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(column)
      setSortOrder('asc')
    }
  }

  const sortedSessions = [...sessions].sort((a, b) => {
    const aVal = a[sortBy]
    const bVal = b[sortBy]
    
    if (typeof aVal === 'string') {
      return sortOrder === 'asc' 
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal)
    } else {
      return sortOrder === 'asc' ? aVal - bVal : bVal - aVal
    }
  })

  if (loading) {
    return <div className="sessions loading">Loading sessions...</div>
  }

  return (
    <div className="sessions">
      <h2>All Sessions</h2>
      
      {sessions.length === 0 ? (
        <p>No sessions found. Start coding with Claude Code to see data here.</p>
      ) : (
        <table className="sessions-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('start_time')}>
                Start Time {sortBy === 'start_time' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('duration_seconds')}>
                Duration {sortBy === 'duration_seconds' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('language')}>
                Language {sortBy === 'language' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('interaction_count')}>
                Interactions {sortBy === 'interaction_count' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('acceptance_rate')}>
                Acceptance {sortBy === 'acceptance_rate' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('status')}>
                Status {sortBy === 'status' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th>Errors</th>
            </tr>
          </thead>
          <tbody>
            {sortedSessions.map(session => (
              <tr key={session.id} className="session-row">
                <td>
                  <Link to={`/session/${session.id}`}>
                    {new Date(session.start_time).toLocaleString()}
                  </Link>
                </td>
                <td>{(session.duration_seconds / 60).toFixed(1)} min</td>
                <td><span className="badge">{session.language}</span></td>
                <td>{session.interaction_count}</td>
                <td>{(session.acceptance_rate * 100).toFixed(1)}%</td>
                <td><span className={`status ${session.status}`}>{session.status}</span></td>
                <td>{session.error_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

export default Sessions
```

---

### 5. components/Charts/Timeline.jsx

```javascript
import React from 'react'
import Plot from 'react-plotly.js'

function Timeline({ data, title, yLabel }) {
  if (!data || data.length === 0) {
    return <div className="chart-placeholder">No data available</div>
  }

  const timestamps = data.map(d => d.timestamp || d.date)
  const values = data.map(d => d.value || d.acceptance_rate || d.rate)

  return (
    <Plot
      data={[
        {
          x: timestamps,
          y: values,
          type: 'scatter',
          mode: 'lines+markers',
          line: { color: '#3B82F6', width: 2 },
          marker: { size: 6, color: '#3B82F6' },
          fill: 'tozeroy',
          fillcolor: 'rgba(59, 130, 246, 0.1)',
          hovertemplate: '<b>%{x}</b><br>%{y:.2f}<extra></extra>',
        }
      ]}
      layout={{
        title,
        xaxis: { title: 'Time' },
        yaxis: { title: yLabel },
        hovermode: 'x unified',
        responsive: true,
        margin: { b: 50, l: 60, r: 40, t: 50 }
      }}
      style={{ width: '100%', height: '400px' }}
    />
  )
}

export default Timeline
```

---

### 6. components/Filters/DateRange.jsx

```javascript
import React, { useState } from 'react'

function DateRange({ onDateChange }) {
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  const handleApply = () => {
    onDateChange(startDate, endDate)
  }

  return (
    <div className="date-range-filter">
      <label>Start Date</label>
      <input
        type="date"
        value={startDate}
        onChange={(e) => setStartDate(e.target.value)}
      />
      
      <label>End Date</label>
      <input
        type="date"
        value={endDate}
        onChange={(e) => setEndDate(e.target.value)}
      />
      
      <button onClick={handleApply}>Apply</button>
    </div>
  )
}

export default DateRange
```

---

### 7. components/Filters/LanguageFilter.jsx

```javascript
import React, { useState, useEffect } from 'react'
import { apiClient } from '../../api/client'

function LanguageFilter({ onLanguageChange }) {
  const [languages, setLanguages] = useState([])
  const [selectedLanguage, setSelectedLanguage] = useState(null)

  useEffect(() => {
    // Fetch available languages from backend
    apiClient.get('/sessions/stats/summary')
      .then(response => {
        const langs = Object.keys(response.data.languages)
        setLanguages(langs)
      })
      .catch(error => console.error('Error fetching languages:', error))
  }, [])

  const handleChange = (e) => {
    const value = e.target.value || null
    setSelectedLanguage(value)
    onLanguageChange(value)
  }

  return (
    <div className="language-filter">
      <label>Programming Language</label>
      <select value={selectedLanguage || ''} onChange={handleChange}>
        <option value="">All Languages</option>
        {languages.map(lang => (
          <option key={lang} value={lang}>{lang}</option>
        ))}
      </select>
    </div>
  )
}

export default LanguageFilter
```

---

### 8. components/InsightsPanel.jsx

```javascript
import React from 'react'

function InsightsPanel({ metrics, sessions }) {
  const insights = []

  // Generate insights
  if (metrics?.byLanguage) {
    const bestLang = Object.entries(metrics.byLanguage)
      .sort((a, b) => b[1] - a[1])[0]
    insights.push({
      title: 'Best Language',
      description: `${bestLang[0]} has ${(bestLang[1] * 100).toFixed(1)}% acceptance rate`
    })
  }

  if (metrics?.errorDistribution) {
    const mostCommon = Object.entries(metrics.errorDistribution)
      .sort((a, b) => b[1] - a[1])[0]
    insights.push({
      title: 'Most Common Error',
      description: `${mostCommon[0]} (${mostCommon[1]} occurrences)`
    })
  }

  // Recovery rate
  if (metrics?.recoveryRate !== undefined) {
    insights.push({
      title: 'Error Recovery',
      description: `${(metrics.recoveryRate * 100).toFixed(1)}% of errors recovered in next interaction`
    })
  }

  return (
    <div className="insights-panel">
      <h3>Key Insights</h3>
      {insights.length > 0 ? (
        <div className="insights-grid">
          {insights.map((insight, index) => (
            <div key={index} className="insight-card">
              <h4>{insight.title}</h4>
              <p>{insight.description}</p>
            </div>
          ))}
        </div>
      ) : (
        <p>No insights available yet. Collect more session data.</p>
      )}
    </div>
  )
}

export default InsightsPanel
```

---

### 9. hooks/useSessions.js

```javascript
import { useState, useEffect } from 'react'
import { apiClient } from '../api/client'

export function useSessions(filters) {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)

    const params = new URLSearchParams()
    if (filters.language) params.append('language', filters.language)
    if (filters.status && filters.status !== 'all') params.append('status', filters.status)
    if (filters.startDate) params.append('start_date', filters.startDate)
    if (filters.endDate) params.append('end_date', filters.endDate)

    apiClient.get(`/sessions?${params.toString()}`)
      .then(response => {
        setSessions(response.data.sessions || [])
      })
      .catch(err => {
        console.error('Error fetching sessions:', err)
        setError(err.message)
      })
      .finally(() => setLoading(false))
  }, [filters])

  return { sessions, loading, error }
}
```

---

### 10. hooks/useMetrics.js

```javascript
import { useState, useEffect } from 'react'
import { apiClient } from '../api/client'

export function useMetrics(filters) {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)

    Promise.all([
      apiClient.get('/metrics/acceptance'),
      apiClient.get('/metrics/errors'),
      apiClient.get('/metrics/quality')
    ])
      .then(([acceptanceRes, errorsRes, qualityRes]) => {
        setMetrics({
          acceptanceTrend: acceptanceRes.data.trend || [],
          byLanguage: acceptanceRes.data.by_language || {},
          errorDistribution: errorsRes.data.error_distribution || {},
          recoveryRate: errorsRes.data.recovery_rate || 0,
          qualityMetrics: qualityRes.data.metrics || []
        })
      })
      .catch(error => console.error('Error fetching metrics:', error))
      .finally(() => setLoading(false))
  }, [filters])

  return { metrics, loading }
}
```

---

### 11. api/client.js

```javascript
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// Error handling
apiClient.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default apiClient
```

---

### 12. styles/globals.css

```css
/* Global styles, reset, variables */

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  --primary: #3B82F6;
  --secondary: #10B981;
  --danger: #EF4444;
  --warning: #F59E0B;
  --bg-primary: #FFFFFF;
  --bg-secondary: #F9FAFB;
  --text-primary: #1F2937;
  --text-secondary: #6B7280;
  --border: #E5E7EB;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  line-height: 1.6;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

button {
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  background-color: var(--primary);
  color: white;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: opacity 0.2s;
}

button:hover {
  opacity: 0.9;
}

input, select {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 14px;
}

table {
  width: 100%;
  border-collapse: collapse;
  background-color: var(--bg-primary);
}

th, td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}

th {
  background-color: var(--bg-secondary);
  font-weight: 600;
  cursor: pointer;
}

tr:hover {
  background-color: var(--bg-secondary);
}

.badge {
  display: inline-block;
  padding: 4px 8px;
  background-color: var(--primary);
  color: white;
  border-radius: 4px;
  font-size: 12px;
}
```

---

## Running the Frontend

```bash
cd frontend
npm install
npm run dev

# Frontend will open at http://localhost:5173
```

---

## Environment Variables

Create `.env` file in frontend/:
```
VITE_API_URL=http://localhost:8000
```

---

## Key Features for MVP

1. **Dashboard page** with KPIs, filters, and charts
2. **Sessions page** with sortable, filterable table
3. **Date range filter** with start/end date pickers
4. **Language filter** with dropdown
5. **Acceptance rate timeline** showing trend
6. **Error distribution heatmap** by type and phase
7. **Scatter plot** of duration vs interactions
8. **Insights panel** with auto-generated recommendations

---

## Chart Libraries

- **Plotly.js**: Interactive, responsive charts
  - Supported: line, scatter, heatmap, bar, pie, box
  - Features: zoom, pan, hover tooltip, export

- **Lucide-react** (optional): Icons for UI
  - Small, lightweight icon library

---

## Styling Approach

For MVP, use plain CSS with CSS variables for theming. Optional upgrades:
- Tailwind CSS
- CSS-in-JS (styled-components)
- Sass/SCSS

Choose based on preference. Plain CSS is simplest for MVP.

---

## Future Enhancements

- Dark mode toggle
- Real-time WebSocket updates (watch dashboard update as you code)
- 3D visualization (session trajectories in embedding space)
- Export reports (PDF, CSV)
- Custom themes
