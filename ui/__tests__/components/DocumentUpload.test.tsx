import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import DocumentUpload from '@/components/DocumentUpload'
import { uploadDocument } from '@/lib/api-client'

// Mock the API client
jest.mock('@/lib/api-client')
const mockUploadDocument = uploadDocument as jest.MockedFunction<typeof uploadDocument>

describe('DocumentUpload', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('File Selection and Validation', () => {
    it('should accept PDF files', async () => {
      const user = userEvent.setup()
      render(<DocumentUpload />)

      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' })
      const input = screen.getByLabelText(/upload/i) as HTMLInputElement

      await user.upload(input, file)

      expect(input.files?.[0]).toBe(file)
      expect(input.files).toHaveLength(1)
    })

    it('should reject non-PDF files', async () => {
      const user = userEvent.setup()
      render(<DocumentUpload />)

      const file = new File(['test content'], 'test.txt', { type: 'text/plain' })
      const input = screen.getByLabelText(/upload/i) as HTMLInputElement

      await user.upload(input, file)

      expect(screen.getByRole('alert')).toHaveTextContent(/only pdf files are allowed/i)
    })

    it('should reject files larger than size limit', async () => {
      const user = userEvent.setup()
      render(<DocumentUpload />)

      // Create a large file (> 50MB)
      const largeFile = new File(['x'.repeat(52 * 1024 * 1024)], 'large.pdf', { 
        type: 'application/pdf' 
      })
      const input = screen.getByLabelText(/upload/i) as HTMLInputElement

      await user.upload(input, largeFile)

      expect(screen.getByRole('alert')).toHaveTextContent(/file size too large/i)
    })
  })

  describe('Upload Process', () => {
    it('should initiate upload for valid files', async () => {
      const user = userEvent.setup()
      mockUploadDocument.mockResolvedValueOnce({
        documentId: 'doc-123',
        filename: 'test.pdf',
        status: 'uploading'
      })

      render(<DocumentUpload />)

      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' })
      const input = screen.getByLabelText(/upload/i) as HTMLInputElement

      await user.upload(input, file)
      
      // Should show upload button for valid file
      const uploadButton = screen.getByRole('button', { name: /upload/i })
      await user.click(uploadButton)

      expect(mockUploadDocument).toHaveBeenCalledWith(
        file,
        expect.any(Function) // progress callback
      )
    })

    it('should show upload progress', async () => {
      const user = userEvent.setup()
      let progressCallback: (progress: any) => void

      mockUploadDocument.mockImplementationOnce((file, callback) => {
        progressCallback = callback
        return new Promise((resolve) => {
          setTimeout(() => {
            progressCallback({ percentage: 50, status: 'uploading' })
            setTimeout(() => {
              progressCallback({ percentage: 100, status: 'complete' })
              resolve({
                documentId: 'doc-123',
                filename: 'test.pdf',
                status: 'complete'
              })
            }, 100)
          }, 100)
        })
      })

      render(<DocumentUpload />)

      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' })
      const input = screen.getByLabelText(/upload/i) as HTMLInputElement

      await user.upload(input, file)
      const uploadButton = screen.getByRole('button', { name: /upload/i })
      await user.click(uploadButton)

      // Should show initial uploading state
      expect(screen.getByText(/uploading/i)).toBeInTheDocument()

      // Wait for progress updates
      await waitFor(() => {
        expect(screen.getByText(/50%/)).toBeInTheDocument()
      })

      await waitFor(() => {
        expect(screen.getByText(/upload complete/i)).toBeInTheDocument()
      })
    })

    it('should handle upload errors gracefully', async () => {
      const user = userEvent.setup()
      mockUploadDocument.mockRejectedValueOnce(new Error('Upload failed'))

      render(<DocumentUpload />)

      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' })
      const input = screen.getByLabelText(/upload/i) as HTMLInputElement

      await user.upload(input, file)
      const uploadButton = screen.getByRole('button', { name: /upload/i })
      await user.click(uploadButton)

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/upload failed/i)
      })

      // Should show retry option
      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
    })
  })

  describe('Multiple File Handling', () => {
    it('should handle multiple file selection', async () => {
      const user = userEvent.setup()
      render(<DocumentUpload />)

      const files = [
        new File(['content1'], 'file1.pdf', { type: 'application/pdf' }),
        new File(['content2'], 'file2.pdf', { type: 'application/pdf' })
      ]
      const input = screen.getByLabelText(/upload/i) as HTMLInputElement

      await user.upload(input, files)

      expect(input.files).toHaveLength(2)
      expect(screen.getByText('file1.pdf')).toBeInTheDocument()
      expect(screen.getByText('file2.pdf')).toBeInTheDocument()
    })

    it('should upload multiple files sequentially', async () => {
      const user = userEvent.setup()
      mockUploadDocument
        .mockResolvedValueOnce({
          documentId: 'doc-1',
          filename: 'file1.pdf', 
          status: 'complete'
        })
        .mockResolvedValueOnce({
          documentId: 'doc-2',
          filename: 'file2.pdf',
          status: 'complete'
        })

      render(<DocumentUpload />)

      const files = [
        new File(['content1'], 'file1.pdf', { type: 'application/pdf' }),
        new File(['content2'], 'file2.pdf', { type: 'application/pdf' })
      ]
      const input = screen.getByLabelText(/upload/i) as HTMLInputElement

      await user.upload(input, files)
      const uploadButton = screen.getByRole('button', { name: /upload all/i })
      await user.click(uploadButton)

      await waitFor(() => {
        expect(mockUploadDocument).toHaveBeenCalledTimes(2)
      })
    })
  })

  describe('UI States and Accessibility', () => {
    it('should be keyboard accessible', async () => {
      render(<DocumentUpload />)

      const input = screen.getByLabelText(/upload/i)
      
      expect(input).toHaveAttribute('type', 'file')
      expect(input).toHaveAttribute('accept', '.pdf,application/pdf')
      
      // Should be focusable
      input.focus()
      expect(input).toHaveFocus()
    })

    it('should show appropriate loading states', async () => {
      const user = userEvent.setup()
      mockUploadDocument.mockImplementationOnce(() => 
        new Promise(resolve => setTimeout(resolve, 1000))
      )

      render(<DocumentUpload />)

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
      const input = screen.getByLabelText(/upload/i) as HTMLInputElement

      await user.upload(input, file)
      const uploadButton = screen.getByRole('button', { name: /upload/i })
      
      await user.click(uploadButton)
      
      expect(uploadButton).toBeDisabled()
      expect(screen.getByText(/uploading/i)).toBeInTheDocument()
    })

    it('should clear form after successful upload', async () => {
      const user = userEvent.setup()
      mockUploadDocument.mockResolvedValueOnce({
        documentId: 'doc-123',
        filename: 'test.pdf',
        status: 'complete'
      })

      render(<DocumentUpload />)

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
      const input = screen.getByLabelText(/upload/i) as HTMLInputElement

      await user.upload(input, file)
      const uploadButton = screen.getByRole('button', { name: /upload/i })
      await user.click(uploadButton)

      await waitFor(() => {
        expect(screen.getByText(/upload complete/i)).toBeInTheDocument()
      })

      // Form should be reset for next upload
      expect(input.value).toBe('')
    })
  })
})