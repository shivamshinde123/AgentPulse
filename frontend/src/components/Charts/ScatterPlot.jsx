import Plot from 'react-plotly.js'

function ScatterPlot({ data, xKey, yKey, sizeKey, title }) {
  if (!data || data.length === 0) {
    return <div className="chart-placeholder">No scatter data available</div>
  }

  // Convert duration to minutes for consistent display
  const toMinutes = xKey === 'duration_seconds'
  const xValues = data.map((d) => {
    const raw = d[xKey] ?? 0
    return toMinutes ? +(raw / 60).toFixed(1) : raw
  })
  const yValues = data.map((d) => d[yKey] ?? 0)
  const sizeValues = sizeKey
    ? data.map((d) => Math.max((d[sizeKey] ?? 0) * 5 + 8, 8))
    : data.map(() => 10)
  const hoverText = data.map(
    (d) =>
      `Language: ${d.language || 'N/A'}<br>` +
      `Duration: ${((d.duration_seconds || 0) / 60).toFixed(1)} min<br>` +
      `Interactions: ${d.interaction_count || 0}<br>` +
      `Errors: ${d.error_count || 0}`
  )

  // Color by language
  const languages = [...new Set(data.map((d) => d.language))]
  const colorMap = {}
  const palette = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4']
  languages.forEach((lang, i) => {
    colorMap[lang] = palette[i % palette.length]
  })
  const colors = data.map((d) => colorMap[d.language] || '#6B7280')

  const xLabel = toMinutes ? 'Duration (minutes)' : xKey
  const yLabel = yKey === 'interaction_count' ? 'Interactions' : yKey

  return (
    <Plot
      data={[
        {
          x: xValues,
          y: yValues,
          type: 'scatter',
          mode: 'markers',
          marker: {
            size: sizeValues,
            color: colors,
            opacity: 0.7,
            line: { width: 1, color: '#fff' },
          },
          text: hoverText,
          hoverinfo: 'text',
        },
      ]}
      layout={{
        title: { text: title, font: { size: 14 } },
        xaxis: { title: xLabel },
        yaxis: { title: yLabel },
        margin: { b: 60, l: 60, r: 30, t: 40 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        hovermode: 'closest',
      }}
      useResizeHandler
      style={{ width: '100%', height: '100%' }}
      config={{ displayModeBar: false, responsive: true }}
    />
  )
}

export default ScatterPlot
