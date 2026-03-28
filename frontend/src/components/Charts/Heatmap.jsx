import Plot from 'react-plotly.js'

function Heatmap({ data, title }) {
  if (!data || Object.keys(data).length === 0) {
    return <div className="chart-placeholder">No error data available</div>
  }

  // data is an object like { syntax: 10, runtime: 5, type: 2, logic: 1 }
  const errorTypes = Object.keys(data)
  const counts = Object.values(data)

  return (
    <Plot
      data={[
        {
          x: errorTypes,
          y: counts,
          type: 'bar',
          marker: {
            color: counts.map((_, i) => {
              const colors = ['#EF4444', '#F59E0B', '#3B82F6', '#10B981', '#8B5CF6', '#EC4899']
              return colors[i % colors.length]
            }),
            line: { width: 0 },
          },
          hovertemplate: '<b>%{x}</b><br>Count: %{y}<extra></extra>',
        },
      ]}
      layout={{
        title: { text: title, font: { size: 14 } },
        xaxis: { title: 'Error Type' },
        yaxis: { title: 'Count' },
        margin: { b: 60, l: 60, r: 30, t: 40 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        bargap: 0.3,
      }}
      useResizeHandler
      style={{ width: '100%', height: '100%' }}
      config={{ displayModeBar: false, responsive: true }}
    />
  )
}

export default Heatmap
