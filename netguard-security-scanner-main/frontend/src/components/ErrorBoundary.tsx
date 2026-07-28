import { Component, ErrorInfo, ReactNode } from 'react'
import { FiAlertTriangle } from 'react-icons/fi'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  errorMessage: string | null
}

/**
 * Class component is required here - React only supports error boundaries
 * via getDerivedStateFromError/componentDidCatch, which have no hook
 * equivalent. Wraps the whole app so an unexpected render error surfaces
 * a recoverable screen instead of a blank white page.
 */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, errorMessage: null }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, errorMessage: error.message }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // In a production deployment this is where you'd forward to an error
    // tracking service (Sentry, etc). Logged to console here to keep the
    // project dependency-free.
    console.error('Unhandled UI error:', error, info.componentStack)
  }

  handleReload = () => {
    this.setState({ hasError: false, errorMessage: null })
    window.location.href = '/'
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-surface-light dark:bg-surface-dark px-4">
          <div className="max-w-md text-center">
            <div className="w-14 h-14 rounded-2xl bg-red-500/10 flex items-center justify-center mx-auto mb-4">
              <FiAlertTriangle className="text-red-500 w-7 h-7" />
            </div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white mb-2">Something went wrong</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
              An unexpected error occurred while rendering the app.
              {this.state.errorMessage && (
                <span className="block mt-2 font-mono text-xs bg-slate-100 dark:bg-slate-800 rounded-lg p-2">
                  {this.state.errorMessage}
                </span>
              )}
            </p>
            <button onClick={this.handleReload} className="btn-primary px-5 py-2.5">
              Reload App
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
