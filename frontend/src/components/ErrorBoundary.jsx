import React from 'react'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    console.error('Unhandled render error:', error, info.componentStack)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-state" role="alert">
          <h3>Something went wrong</h3>
          <p>{this.state.error?.message || 'An unexpected error occurred.'}</p>
          <button
            className="btn"
            onClick={() => window.location.reload()}
          >
            Reload Page
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

export default ErrorBoundary
