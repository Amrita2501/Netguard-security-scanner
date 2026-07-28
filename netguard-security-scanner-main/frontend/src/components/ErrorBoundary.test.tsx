import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import ErrorBoundary from '../components/ErrorBoundary'

function ThrowingComponent(): JSX.Element {
  throw new Error('Simulated render failure')
}

describe('ErrorBoundary', () => {
  it('renders children normally when there is no error', () => {
    render(
      <ErrorBoundary>
        <p>All good</p>
      </ErrorBoundary>
    )
    expect(screen.getByText('All good')).toBeInTheDocument()
  })

  it('renders a fallback screen instead of crashing when a child throws', () => {
    // React logs the caught error to the console by design; silence it so
    // the test output stays clean without hiding a genuine assertion failure.
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    render(
      <ErrorBoundary>
        <ThrowingComponent />
      </ErrorBoundary>
    )

    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    expect(screen.getByText('Simulated render failure')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reload App' })).toBeInTheDocument()

    consoleSpy.mockRestore()
  })
})
