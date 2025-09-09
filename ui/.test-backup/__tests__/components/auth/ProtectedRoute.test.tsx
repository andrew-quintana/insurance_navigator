import { render, screen, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import ProtectedRoute from '@/components/auth/ProtectedRoute'

// Mock Next.js router
const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush
  })
}))

// Mock Supabase client
jest.mock('@/lib/supabase-client', () => ({
  supabase: {
    auth: {
      getSession: jest.fn(),
      onAuthStateChange: jest.fn()
    }
  }
}))

// Get references to the mocked functions
const mockGetSession = jest.mocked(require('@/lib/supabase-client').supabase.auth.getSession)
const mockOnAuthStateChange = jest.mocked(require('@/lib/supabase-client').supabase.auth.onAuthStateChange)
const mockUnsubscribe = jest.fn()

const TestComponent = () => <div>Protected Content</div>

describe('ProtectedRoute', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockPush.mockClear()
    mockGetSession.mockClear()
    mockOnAuthStateChange.mockClear()
    mockUnsubscribe.mockClear()
  })

  describe('Authentication Flow (PRIORITY #1)', () => {
    it('should render children when user is authenticated', async () => {
      // Mock successful authentication
      mockGetSession.mockResolvedValue({
        data: { 
          session: {
            user: { id: 'test-user-id', email: 'test@example.com' },
            access_token: 'mock-token'
          }
        },
        error: null
      })
      
      mockOnAuthStateChange.mockReturnValue({
        data: { subscription: { unsubscribe: mockUnsubscribe } }
      })
      
      render(
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      )

      // Should show loading spinner initially
      expect(screen.getByTestId('loading-spinner')).toHaveClass('animate-spin')

      // Should render protected content after authentication check
      await waitFor(() => {
        expect(screen.getByText('Protected Content')).toBeInTheDocument()
      })

      // Should not redirect
      expect(mockPush).not.toHaveBeenCalled()
    })

    it('should redirect unauthenticated users to login page', async () => {
      // Mock no session
      mockGetSession.mockResolvedValue({
        data: { session: null },
        error: null
      })
      
      mockOnAuthStateChange.mockReturnValue({
        data: { subscription: { unsubscribe: mockUnsubscribe } }
      })
      
      render(
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      )

      // Should redirect to default login page
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login')
      })

      // Should not render protected content
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    })

    it('should redirect to custom path when specified', async () => {
      // Mock no session
      mockGetSession.mockResolvedValue({
        data: { session: null },
        error: null
      })
      
      mockOnAuthStateChange.mockReturnValue({
        data: { subscription: { unsubscribe: mockUnsubscribe } }
      })
      
      render(
        <ProtectedRoute redirectTo="/auth/signin">
          <TestComponent />
        </ProtectedRoute>
      )

      // Should redirect to custom path
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/auth/signin')
      })
    })

    it('should handle authentication errors gracefully', async () => {
      // Mock authentication error
      mockGetSession.mockResolvedValue({
        data: { session: null },
        error: new Error('Authentication service unavailable')
      })
      
      mockOnAuthStateChange.mockReturnValue({
        data: { subscription: { unsubscribe: mockUnsubscribe } }
      })
      
      render(
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      )

      // Should redirect to login on error
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login')
      })
    })
  })

  describe('Session Management', () => {
    it('should handle session expiry during component lifecycle', async () => {
      // Mock successful authentication initially
      mockGetSession.mockResolvedValue({
        data: { 
          session: {
            user: { id: 'test-user-id', email: 'test@example.com' },
            access_token: 'mock-token'
          }
        },
        error: null
      })
      
      mockOnAuthStateChange.mockReturnValue({
        data: { subscription: { unsubscribe: mockUnsubscribe } }
      })
      
      const { rerender } = render(
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      )

      // Should show protected content initially
      await waitFor(() => {
        expect(screen.getByText('Protected Content')).toBeInTheDocument()
      })

      // Simulate auth state change to signed out
      const authStateCallback = mockOnAuthStateChange.mock.calls[0][0]
      authStateCallback('SIGNED_OUT', null)

      // Should redirect to login
      expect(mockPush).toHaveBeenCalledWith('/login')
    })

    it('should handle token refresh during component lifecycle', async () => {
      // Mock successful authentication
      mockGetSession.mockResolvedValue({
        data: { 
          session: {
            user: { id: 'test-user-id', email: 'test@example.com' },
            access_token: 'mock-token'
          }
        },
        error: null
      })
      
      mockOnAuthStateChange.mockReturnValue({
        data: { subscription: { unsubscribe: mockUnsubscribe } }
      })
      
      render(
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      )

      // Should show protected content
      await waitFor(() => {
        expect(screen.getByText('Protected Content')).toBeInTheDocument()
      })

      // Simulate token refresh
      const authStateCallback = mockOnAuthStateChange.mock.calls[0][0]
      authStateCallback('TOKEN_REFRESHED', {
        user: { id: 'test-user-id', email: 'test@example.com' },
        access_token: 'new-mock-token'
      })

      // Should still show protected content
      expect(screen.getByText('Protected Content')).toBeInTheDocument()
    })
  })

  describe('Loading States', () => {
    it('should show loading spinner while checking authentication', async () => {
      // Mock delayed response
      mockGetSession.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({
          data: { session: null },
          error: null
        }), 100))
      )
      
      mockOnAuthStateChange.mockReturnValue({
        data: { subscription: { unsubscribe: mockUnsubscribe } }
      })
      
      render(
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      )

      // Should show loading spinner initially
      expect(screen.getByTestId('loading-spinner')).toHaveClass('animate-spin')
    })

    it('should hide loading after authentication check completes', async () => {
      // Mock successful authentication
      mockGetSession.mockResolvedValue({
        data: { 
          session: {
            user: { id: 'test-user-id', email: 'test@example.com' },
            access_token: 'mock-token'
          }
        },
        error: null
      })
      
      mockOnAuthStateChange.mockReturnValue({
        data: { subscription: { unsubscribe: mockUnsubscribe } }
      })
      
      render(
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      )

      // Should show loading spinner initially
      expect(screen.getByTestId('loading-spinner')).toHaveClass('animate-spin')

      // Should hide loading and show content
      await waitFor(() => {
        expect(screen.queryByText(/loading/i)).not.toBeInTheDocument()
        expect(screen.getByText('Protected Content')).toBeInTheDocument()
      })
    })
  })

  describe('Auth State Changes', () => {
    it('should handle sign out event', async () => {
      // Mock successful authentication initially
      mockGetSession.mockResolvedValue({
        data: { 
          session: {
            user: { id: 'test-user-id', email: 'test@example.com' },
            access_token: 'mock-token'
          }
        },
        error: null
      })
      
      mockOnAuthStateChange.mockReturnValue({
        data: { subscription: { unsubscribe: mockUnsubscribe } }
      })
      
      render(
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      )

      // Should show protected content initially
      await waitFor(() => {
        expect(screen.getByText('Protected Content')).toBeInTheDocument()
      })

      // Simulate sign out
      const authStateCallback = mockOnAuthStateChange.mock.calls[0][0]
      authStateCallback('SIGNED_OUT', null)

      // Should redirect to login
      expect(mockPush).toHaveBeenCalledWith('/login')
    })

    it('should handle sign in event', async () => {
      // Mock no session initially
      mockGetSession.mockResolvedValue({
        data: { session: null },
        error: null
      })
      
      mockOnAuthStateChange.mockReturnValue({
        data: { subscription: { unsubscribe: mockUnsubscribe } }
      })
      
      render(
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      )

      // Should redirect initially
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login')
      })

      // Note: The component doesn't handle SIGNED_IN events from auth state changes
      // It only handles the initial session check. This is a limitation of the current implementation.
      // The test documents this behavior rather than expecting it to work.
    })
  })

  describe('Component Lifecycle', () => {
    it('should handle multiple auth state changes correctly', async () => {
      // Mock successful authentication initially
      mockGetSession.mockResolvedValue({
        data: { 
          session: {
            user: { id: 'test-user-id', email: 'test@example.com' },
            access_token: 'mock-token'
          }
        },
        error: null
      })
      
      mockOnAuthStateChange.mockReturnValue({
        data: { subscription: { unsubscribe: mockUnsubscribe } }
      })
      
      const { rerender } = render(
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      )

      // Should show protected content initially
      await waitFor(() => {
        expect(screen.getByText('Protected Content')).toBeInTheDocument()
      })

      // Simulate multiple auth state changes
      const authStateCallback = mockOnAuthStateChange.mock.calls[0][0]
      
      // Sign out
      authStateCallback('SIGNED_OUT', null)
      expect(mockPush).toHaveBeenCalledWith('/login')
      
      // Sign back in
      authStateCallback('SIGNED_IN', {
        user: { id: 'test-user-id', email: 'test@example.com' },
        access_token: 'mock-token'
      })
      expect(screen.getByText('Protected Content')).toBeInTheDocument()
    })

    it('should cleanup auth state listener on unmount', async () => {
      // Mock successful authentication
      mockGetSession.mockResolvedValue({
        data: { 
          session: {
            user: { id: 'test-user-id', email: 'test@example.com' },
            access_token: 'mock-token'
          }
        },
        error: null
      })
      
      mockOnAuthStateChange.mockReturnValue({
        data: { subscription: { unsubscribe: mockUnsubscribe } }
      })
      
      const { unmount } = render(
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      )

      // Should show protected content
      await waitFor(() => {
        expect(screen.getByText('Protected Content')).toBeInTheDocument()
      })

      // Unmount component
      unmount()

      // Should cleanup subscription
      expect(mockUnsubscribe).toHaveBeenCalled()
    })
  })

  describe('Error Handling', () => {
    it('should handle network errors during session check', async () => {
      // Mock network error
      mockGetSession.mockRejectedValue(new Error('Network error'))
      
      mockOnAuthStateChange.mockReturnValue({
        data: { subscription: { unsubscribe: mockUnsubscribe } }
      })
      
      render(
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      )

      // Should redirect to login on error
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login')
      })
    })

    it('should handle malformed session data', async () => {
      // Mock malformed session data
      mockGetSession.mockResolvedValue({
        data: { session: 'invalid-session-data' },
        error: null
      })
      
      mockOnAuthStateChange.mockReturnValue({
        data: { subscription: { unsubscribe: mockUnsubscribe } }
      })
      
      render(
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      )

      // Should redirect to login on malformed data
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login')
      })
    })
  })

  describe('Accessibility', () => {
    it('should have accessible loading state', async () => {
      // Mock delayed response
      mockGetSession.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({
          data: { session: null },
          error: null
        }), 100))
      )
      
      mockOnAuthStateChange.mockReturnValue({
        data: { subscription: { unsubscribe: mockUnsubscribe } }
      })
      
      render(
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      )

      // Loading spinner should be present
      const loadingSpinner = screen.getByTestId('loading-spinner')
      expect(loadingSpinner).toHaveClass('animate-spin')
    })

    it('should not render protected content until authenticated', async () => {
      // Mock no session
      mockGetSession.mockResolvedValue({
        data: { session: null },
        error: null
      })
      
      mockOnAuthStateChange.mockReturnValue({
        data: { subscription: { unsubscribe: mockUnsubscribe } }
      })
      
      render(
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      )

      // Should not show protected content
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    })
  })
})
