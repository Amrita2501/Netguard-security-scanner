import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import RiskBadge from '../../components/Badges/RiskBadge'

describe('RiskBadge', () => {
  it('renders the risk level label', () => {
    render(<RiskBadge level="HIGH" />)
    expect(screen.getByText('HIGH')).toBeInTheDocument()
  })

  it.each([
    ['LOW', 'text-emerald-700'],
    ['MEDIUM', 'text-amber-700'],
    ['HIGH', 'text-orange-700'],
    ['CRITICAL', 'text-red-700'],
  ] as const)('applies the correct color class for %s risk', (level, expectedClass) => {
    render(<RiskBadge level={level} />)
    expect(screen.getByText(level)).toHaveClass(expectedClass)
  })
})
