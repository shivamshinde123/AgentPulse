import Plot from 'react-plotly.js'

function Timeline({ data, title, yLabel }) {
  if (!data || data.length === 0) {
    return <div className="chart-placeholder">No timeline data available</div>
  }

  const timestamps = data.map((d) => d.timestamp || d.date)
  const values = data.map((d) => d.value ?? d.acceptance_rate ?? d.rate ?? 0)

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
        },
      ]}
      layout={{
        title: { text: title, font: { size: 14 } },
        xaxis: { title: 'Time' },
        yaxis: { title: yLabel },
        hovermode: 'x unified',
        margin: { b: 50, l: 60, r: 30, t: 40 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
      }}
      useResizeHandler
      style={{ width: '100%', height: '100%' }}
      config={{ displayModeBar: false, responsive: true }}
    />
  )
}

export default Timeline
