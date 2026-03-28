import React, { useState } from 'react'

function DateRange({ onDateChange }) {
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  const handleApply = () => {
    onDateChange(startDate || null, endDate || null)
  }

  const handleClear = () => {
    setStartDate('')
    setEndDate('')
    onDateChange(null, null)
  }

  return (
    <div className="date-range-filter">
      <label>Date Range</label>
      <div className="date-inputs">
        <input
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          placeholder="Start"
        />
        <span className="date-separator">to</span>
        <input
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          placeholder="End"
        />
      </div>
      <div className="date-actions">
        <button type="button" className="btn btn-sm" onClick={handleApply}>
          Apply
        </button>
        {(startDate || endDate) && (
          <button type="button" className="btn btn-sm btn-secondary" onClick={handleClear}>
            Clear
          </button>
        )}
      </div>
    </div>
  )
}

export default DateRange
