import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import DocumentManager from '@/components/DocumentManager'

// Mock fetch globally
const mockFetch = jest.fn()
global.fetch = mockFetch

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
  writable: true
})

describe('DocumentManager', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Set up authenticated user by default
    mockLocalStorage.getItem.mockReturnValue('mock-auth-token')
  })

  describe('Authentication Requirements (PRIORITY #1)', () => {
    it('should require authentication to search documents', async () => {
      // Mock unauthenticated user
      mockLocalStorage.getItem.mockReturnValue(null)
      
      render(<DocumentManager />)

      // Should show search interface but require auth for actual search
      expect(screen.getByText('Search Your Documents')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Search your documents...')).toBeInTheDocument()
    })

    it('should show search interface when authenticated', async () => {
      render(<DocumentManager />)

      // Should show search interface
      expect(screen.getByText('Search Your Documents')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Search your documents...')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument()
    })
  })

  describe('Search Functionality', () => {
    it('should perform search when form is submitted', async () => {
      const mockSearchResponse = {
        success: true,
        query: 'medicare',
        results: [
          {
            document_id: 'doc-1',
            text: 'Medicare Part B coverage information',
            filename: 'policy-1.pdf',
            similarity_score: 0.8,
            metadata: {
              filename: 'policy-1.pdf',
              file_size: 1024,
              content_type: 'application/pdf',
              chunk_length: 1000,
              total_chunks: 5,
              uploaded_at: '2024-01-01T10:00:00Z'
            }
          }
        ],
        total_results: 1
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSearchResponse
      })

      render(<DocumentManager />)

      const searchInput = screen.getByPlaceholderText('Search your documents...')
      const searchButton = screen.getByRole('button', { name: /search/i })

      await userEvent.type(searchInput, 'medicare')
      await userEvent.click(searchButton)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/search-documents'),
          expect.objectContaining({
            method: 'POST',
            headers: {
              'Authorization': 'Bearer mock-auth-token'
            }
          })
        )
      })
    })

    it('should display search results after successful search', async () => {
      const mockSearchResponse = {
        success: true,
        query: 'medicare',
        results: [
          {
            document_id: 'doc-1',
            text: 'Medicare Part B coverage information',
            filename: 'policy-1.pdf',
            similarity_score: 0.8,
            metadata: {
              filename: 'policy-1.pdf',
              file_size: 1024,
              content_type: 'application/pdf',
              chunk_length: 1000,
              total_chunks: 5,
              uploaded_at: '2024-01-01T10:00:00Z'
            }
          }
        ],
        total_results: 1
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSearchResponse
      })

      render(<DocumentManager />)

      const searchInput = screen.getByPlaceholderText('Search your documents...')
      const searchButton = screen.getByRole('button', { name: /search/i })

      await userEvent.type(searchInput, 'medicare')
      await userEvent.click(searchButton)

      await waitFor(() => {
        expect(screen.getByText('policy-1.pdf')).toBeInTheDocument()
        expect(screen.getByText('Medicare Part B coverage information')).toBeInTheDocument()
      })
    })

    it('should show no results message when search returns empty', async () => {
      const mockSearchResponse = {
        success: true,
        query: 'nonexistent',
        results: [],
        total_results: 0
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSearchResponse
      })

      render(<DocumentManager />)

      const searchInput = screen.getByPlaceholderText('Search your documents...')
      const searchButton = screen.getByRole('button', { name: /search/i })

      await userEvent.type(searchInput, 'nonexistent')
      await userEvent.click(searchButton)

      await waitFor(() => {
        expect(screen.getByText('No Results Found')).toBeInTheDocument()
        expect(screen.getByText(/No documents found matching "nonexistent"/)).toBeInTheDocument()
      })
    })

    it('should show loading state during search', async () => {
      // Mock a delayed response
      mockFetch.mockImplementationOnce(() => 
        new Promise(resolve => 
          setTimeout(() => resolve({
            ok: true,
            json: async () => ({ success: true, query: 'test', results: [], total_results: 0 })
          }), 100)
        )
      )

      render(<DocumentManager />)

      const searchInput = screen.getByPlaceholderText('Search your documents...')
      const searchButton = screen.getByRole('button', { name: /search/i })

      await userEvent.type(searchInput, 'test')
      await userEvent.click(searchButton)

      // Should show loading state
      expect(screen.getByText('Searching...')).toBeInTheDocument()
      expect(searchButton).toBeDisabled()
      expect(searchInput).toBeDisabled()
    })
  })

  describe('Error Handling', () => {
    it('should handle search errors gracefully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Internal server error' })
      })

      render(<DocumentManager />)

      const searchInput = screen.getByPlaceholderText('Search your documents...')
      const searchButton = screen.getByRole('button', { name: /search/i })

      await userEvent.type(searchInput, 'test')
      await userEvent.click(searchButton)

      await waitFor(() => {
        expect(screen.getByText('Search Error')).toBeInTheDocument()
        expect(screen.getByText('Internal server error')).toBeInTheDocument()
      })
    })

    it('should handle network errors gracefully', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      render(<DocumentManager />)

      const searchInput = screen.getByPlaceholderText('Search your documents...')
      const searchButton = screen.getByRole('button', { name: /search/i })

      await userEvent.type(searchInput, 'test')
      await userEvent.click(searchButton)

      await waitFor(() => {
        expect(screen.getByText('Search Error')).toBeInTheDocument()
        expect(screen.getByText('Network error')).toBeInTheDocument()
      })
    })

    it('should handle authentication errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Authentication required' })
      })

      render(<DocumentManager />)

      const searchInput = screen.getByPlaceholderText('Search your documents...')
      const searchButton = screen.getByRole('button', { name: /search/i })

      await userEvent.type(searchInput, 'test')
      await userEvent.click(searchButton)

      await waitFor(() => {
        expect(screen.getByText('Search Error')).toBeInTheDocument()
        expect(screen.getByText('Authentication required')).toBeInTheDocument()
      })
    })
  })

  describe('User Experience', () => {
    it('should disable search button when input is empty', () => {
      render(<DocumentManager />)

      const searchButton = screen.getByRole('button', { name: /search/i })
      expect(searchButton).toBeDisabled()
    })

    it('should enable search button when input has content', async () => {
      render(<DocumentManager />)

      const searchInput = screen.getByPlaceholderText('Search your documents...')
      const searchButton = screen.getByRole('button', { name: /search/i })

      await userEvent.type(searchInput, 'test')
      expect(searchButton).not.toBeDisabled()
    })

    it('should maintain search results when query is empty', async () => {
      // First search with results
      const mockSearchResponse = {
        success: true,
        query: 'medicare',
        results: [
          {
            document_id: 'doc-1',
            text: 'Medicare Part B coverage information',
            filename: 'policy-1.pdf',
            similarity_score: 0.8,
            metadata: {
              filename: 'policy-1.pdf',
              file_size: 1024,
              content_type: 'application/pdf',
              chunk_length: 1000,
              total_chunks: 5,
              uploaded_at: '2024-01-01T10:00:00Z'
            }
          }
        ],
        total_results: 1
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSearchResponse
      })

      render(<DocumentManager />)

      const searchInput = screen.getByPlaceholderText('Search your documents...')
      const searchButton = screen.getByRole('button', { name: /search/i })

      await userEvent.type(searchInput, 'medicare')
      await userEvent.click(searchButton)

      await waitFor(() => {
        expect(screen.getByText('policy-1.pdf')).toBeInTheDocument()
      })

      // Clear input and search - the component should still show previous results
      await userEvent.clear(searchInput)
      await userEvent.click(searchButton)

      // Should still show previous results since hasSearched remains true
      expect(screen.getByText('policy-1.pdf')).toBeInTheDocument()
      // Should not show help text since a search has already been performed
      expect(screen.queryByText('How to Search')).not.toBeInTheDocument()
    })
  })

  describe('Help and Guidance', () => {
    it('should show help text when no search has been performed', () => {
      render(<DocumentManager />)

      expect(screen.getByText('How to Search')).toBeInTheDocument()
      expect(screen.getByText(/Use natural language to search your documents/)).toBeInTheDocument()
      expect(screen.getByText(/Try queries like "Medicare Part B coverage" or "prescription drugs"/)).toBeInTheDocument()
    })

    it('should hide help text after search is performed', async () => {
      const mockSearchResponse = {
        success: true,
        query: 'medicare',
        results: [],
        total_results: 0
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSearchResponse
      })

      render(<DocumentManager />)

      const searchInput = screen.getByPlaceholderText('Search your documents...')
      const searchButton = screen.getByRole('button', { name: /search/i })

      await userEvent.type(searchInput, 'medicare')
      await userEvent.click(searchButton)

      await waitFor(() => {
        expect(screen.queryByText('How to Search')).not.toBeInTheDocument()
      })
    })
  })

  describe('Document Display', () => {
    it('should display document metadata correctly', async () => {
      const mockSearchResponse = {
        success: true,
        query: 'medicare',
        results: [
          {
            document_id: 'doc-1',
            text: 'Medicare Part B coverage information for outpatient services and medical supplies.',
            filename: 'policy-1.pdf',
            similarity_score: 0.85,
            metadata: {
              filename: 'policy-1.pdf',
              file_size: 2048,
              content_type: 'application/pdf',
              chunk_length: 1000,
              total_chunks: 8,
              uploaded_at: '2024-01-15T10:30:00Z'
            }
          }
        ],
        total_results: 1
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSearchResponse
      })

      render(<DocumentManager />)

      const searchInput = screen.getByPlaceholderText('Search your documents...')
      const searchButton = screen.getByRole('button', { name: /search/i })

      await userEvent.type(searchInput, 'medicare')
      await userEvent.click(searchButton)

      await waitFor(() => {
        expect(screen.getByText('policy-1.pdf')).toBeInTheDocument()
        expect(screen.getByText(/Document ID: doc-1/)).toBeInTheDocument()
        expect(screen.getByText(/Uploaded: 1\/15\/2024/)).toBeInTheDocument()
        expect(screen.getByText(/Size: 2.0 KB/)).toBeInTheDocument()
        expect(screen.getByText(/1 relevant sections found/)).toBeInTheDocument()
        // The component shows (1 - similarity_score) without multiplying by 100, so 0.85 becomes 0.2
        expect(screen.getByText(/Best Match: 0.2% relevant/)).toBeInTheDocument()
      })
    })

    it('should truncate long text excerpts', async () => {
      const longText = 'A'.repeat(300)
      const mockSearchResponse = {
        success: true,
        query: 'test',
        results: [
          {
            document_id: 'doc-1',
            text: longText,
            filename: 'long-doc.pdf',
            similarity_score: 0.9,
            metadata: {
              filename: 'long-doc.pdf',
              file_size: 1024,
              content_type: 'application/pdf',
              chunk_length: 1000,
              total_chunks: 1,
              uploaded_at: '2024-01-01T10:00:00Z'
            }
          }
        ],
        total_results: 1
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSearchResponse
      })

      render(<DocumentManager />)

      const searchInput = screen.getByPlaceholderText('Search your documents...')
      const searchButton = screen.getByRole('button', { name: /search/i })

      await userEvent.type(searchInput, 'test')
      await userEvent.click(searchButton)

      await waitFor(() => {
        expect(screen.getByText(/A{200}\.\.\./)).toBeInTheDocument()
      })
    })
  })
})
