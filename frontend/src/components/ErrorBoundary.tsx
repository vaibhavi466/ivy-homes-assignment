import {
  Component,
  type ReactNode,
} from 'react'

interface ErrorBoundaryProps {
  children: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
}

export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = {
    hasError: false,
  }

  static getDerivedStateFromError():
    ErrorBoundaryState {
    return {
      hasError: true,
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className="error-boundary">
          <div
            className="state-card error-state"
            role="alert"
          >
            <p className="page-eyebrow">
              Application error
            </p>

            <h1>
              Something went wrong
            </h1>

            <p>
              The application hit an
              unexpected error. Your
              saved browser data has
              not been removed.
            </p>

            <button
              type="button"
              onClick={() =>
                window.location.reload()
              }
            >
              Reload application
            </button>
          </div>
        </main>
      )
    }

    return this.props.children
  }
}
