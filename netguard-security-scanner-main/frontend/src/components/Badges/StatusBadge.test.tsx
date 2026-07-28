import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import StatusBadge from '../../components/Badges/StatusBadge'

describe('StatusBadge', () => {
  it('shows "Online" for an online host', () => {
    render(<StatusBadge status="online" />)
    expect(screen.getByText('Online')).toBeInTheDocument()
  })

  it('shows "Offline" for an offline host', () => {
    render(<StatusBadge status="offline" />)
    expect(screen.getByText('Offline')).toBeInTheDocument()
  })
})
