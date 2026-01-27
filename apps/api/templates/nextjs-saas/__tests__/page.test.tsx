import { render, screen } from '@testing-library/react'
import Home from '../app/page'

describe('Home Page', () => {
  it('renders welcome message', () => {
    render(<Home />)
    expect(screen.getByText(/Welcome to/i)).toBeInTheDocument()
  })
})
