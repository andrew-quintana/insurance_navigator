'use client'

import React, { useRef, useState, useCallback } from 'react'
import { Upload, File, CheckCircle, AlertCircle, X, Clock } from 'lucide-react'
import { Card } from '@/components/ui/card'

interface UploadResponse {
  success: boolean
  document_id: string
  filename: string
  chunks_processed: number
  total_chunks: number
  text_length: number
  message: string
}

interface FileUploadStatus {
  file: File
  status: 'pending' | 'uploading' | 'complete' | 'error'
  progress: number
  documentId?: string
  error?: string
}

interface DocumentUploadProps {
  onUploadSuccess?: (result: UploadResponse) => void
  onUploadError?: (error: string) => void
  className?: string
}

export default function DocumentUploadServerless({ 
  onUploadSuccess, 
  onUploadError,
  className = ""
}: DocumentUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [selectedFiles, setSelectedFiles] = useState<FileUploadStatus[]>([])
  const [isDragOver, setIsDragOver] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // File validation
  const validateFile = (file: File): string | null => {
    const maxSize = 50 * 1024 * 1024 // 50MB
    const allowedTypes = [
      'application/pdf',
      'text/plain',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword'
    ]

    if (file.size > maxSize) {
      return 'File size must be less than 50MB'
    }

    if (!allowedTypes.includes(file.type)) {
      return 'Only PDF, DOC, DOCX, and TXT files are supported'
    }

    return null
  }

  // Handle file selection for multiple files
  const handleFileSelect = useCallback((files: File[]) => {
    const newFiles = files.map(file => {
      const validation = validateFile(file)
      if (validation) {
        return {
          file,
          status: 'error' as const,
          progress: 0,
          error: validation
        }
      }
      return {
        file,
        status: 'pending' as const,
        progress: 0
      }
    })

    setSelectedFiles(prev => [...prev, ...newFiles])
    setError(null)
  }, [])

  // Handle drag events
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  // Update drop handler for multiple files
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      handleFileSelect(files)
    }
  }, [handleFileSelect])

  // Update file input change handler for multiple files
  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFileSelect(Array.from(files))
    }
  }, [handleFileSelect])

  // Upload single file
  const uploadFile = async (fileStatus: FileUploadStatus): Promise<UploadResponse> => {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || '***REMOVED***'
    const uploadEndpoint = `${apiBaseUrl}/api/upload-pipeline/upload`
    
    // Get token from Supabase session if not in localStorage
    let token = localStorage.getItem("token")
    if (!token) {
      // Try to get token from Supabase session
      const { createClient } = await import('@supabase/supabase-js')
      const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
      const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
      
      if (supabaseUrl && supabaseAnonKey) {
        const supabase = createClient(supabaseUrl, supabaseAnonKey)
        const { data: { session } } = await supabase.auth.getSession()
        
        if (session?.access_token) {
          token = session.access_token
          localStorage.setItem('token', token)
        }
      }
    }
    
    console.log('🔍 Debug - Upload starting:', {
      fileName: fileStatus.file.name,
      fileSize: fileStatus.file.size,
      fileType: fileStatus.file.type,
      uploadEndpoint,
      hasToken: !!token
    })
    
    // Validate file before upload
    const validation = validateFile(fileStatus.file)
    if (validation) {
      throw new Error(validation)
    }
    
    // Read file content for metadata calculation
    const fileContent = await fileStatus.file.arrayBuffer()
    const fileSize = fileContent.byteLength
    const fileHash = await crypto.subtle.digest('SHA-256', fileContent)
    const fileSha256 = Array.from(new Uint8Array(fileHash))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('')
    
    // Create upload request payload
    const uploadRequest = {
      filename: fileStatus.file.name,
      bytes_len: fileSize,
      mime: fileStatus.file.type || "application/octet-stream",
      sha256: fileSha256,
      ocr: false
    }
    
    console.log('📤 Debug - Preparing upload:', {
      uploadRequest,
      endpoint: uploadEndpoint
    })
    
    try {
      const uploadResponse = await fetch(uploadEndpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(uploadRequest),
      })

      console.log('📥 Debug - Response received:', {
        status: uploadResponse.status,
        ok: uploadResponse.ok,
        statusText: uploadResponse.statusText,
        headers: Object.fromEntries(uploadResponse.headers.entries())
      })

      if (!uploadResponse.ok) {
        const errorText = await uploadResponse.text()
        console.error('❌ Upload failed:', {
          status: uploadResponse.status,
          statusText: uploadResponse.statusText,
          error: errorText
        })
        
        // Handle duplicate file case
        if (uploadResponse.status === 409) {
          const errorData = JSON.parse(errorText)
          return {
            success: true,
            document_id: errorData.documentId,
            filename: errorData.filename,
            chunks_processed: 1,
            total_chunks: 1,
            text_length: 0,
            message: 'Document already exists and will be used'
          }
        }
        
        throw new Error(`Upload failed (${uploadResponse.status}): ${errorText}`)
      }

      const result = await uploadResponse.json()
      console.log('✅ Upload request successful:', result)
      
      // Now upload the actual file using the signed URL
      if (result.signed_url) {
        console.log('📤 Uploading file to signed URL...')
        
        const fileUploadResponse = await fetch(result.signed_url, {
          method: 'PUT',
          headers: {
            'Content-Type': fileStatus.file.type || 'application/octet-stream',
          },
          body: fileStatus.file
        })
        
        if (!fileUploadResponse.ok) {
          throw new Error(`File upload failed: ${fileUploadResponse.status} ${fileUploadResponse.statusText}`)
        }
        
        console.log('✅ File upload successful')
      }
      
      return {
        success: true,
        document_id: result.document_id || result.id || 'unknown',
        filename: fileStatus.file.name,
        chunks_processed: result.chunks_processed || 1,
        total_chunks: result.total_chunks || 1,
        text_length: result.text_length || 0,
        message: result.message || 'Document processed successfully!'
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'
      console.error('❌ Upload error:', {
        error: err,
        message: errorMessage
      })
      throw new Error(`Upload failed: ${errorMessage}`)
    }
  }

  // Upload all files
  const handleUpload = async () => {
    console.log('🚀 Debug - Upload handler started', {
      fileCount: selectedFiles.length,
      isUploading,
      files: selectedFiles.map(f => ({
        name: f.file.name,
        size: f.file.size,
        type: f.file.type,
        status: f.status
      }))
    })

    if (selectedFiles.length === 0) {
      console.log('⚠️ Debug - No files selected')
      return
    }
    if (isUploading) {
      console.log('⚠️ Debug - Already uploading')
      return
    }

    setIsUploading(true)
    setError(null)

    try {
      console.log('📁 Debug - Processing files:', selectedFiles.length)
      
      for (const fileStatus of selectedFiles) {
        console.log('📄 Debug - Processing file:', fileStatus.file.name)
        try {
          const result = await uploadFile(fileStatus)
          
          console.log('✅ Debug - Upload successful:', fileStatus.file.name)
          setSelectedFiles(prev => prev.map(f => 
            f.file.name === fileStatus.file.name 
              ? { ...f, status: 'complete', progress: 100, documentId: result.document_id }
              : f
          ))

          if (onUploadSuccess) {
            onUploadSuccess(result)
          }
        } catch (error: unknown) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error'
          console.error('❌ Debug - File upload failed:', fileStatus.file.name, error)
          setSelectedFiles(prev => prev.map(f => 
            f.file.name === fileStatus.file.name 
              ? { ...f, status: 'error', error: errorMessage } 
              : f
          ))
          if (onUploadError) {
            onUploadError(errorMessage)
          }
        }
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      console.error('❌ Debug - Upload handler error:', error)
      setError(errorMessage)
    } finally {
      setIsUploading(false)
      console.log('🏁 Debug - Upload handler completed')
    }
  }

  const removeFile = (file: File) => {
    setSelectedFiles(prev => prev.filter(f => f.file !== file))
  }

  const resetUpload = () => {
    setSelectedFiles([])
    setError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <Card className={`p-6 ${className}`}>
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center ${
          isDragOver ? 'border-teal-500 bg-teal-50' : 'border-gray-300'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileInputChange}
          className="hidden"
          multiple
          accept=".pdf,.doc,.docx,.txt"
        />

        <Upload className="mx-auto h-12 w-12 text-gray-400" />
        
        <h3 className="mt-4 text-lg font-semibold text-gray-900">
          Upload Your Documents
        </h3>
        
        <p className="mt-2 text-sm text-gray-600">
          Drag and drop your files here, or{' '}
          <button
            type="button"
            className="text-teal-600 hover:text-teal-500 font-medium"
            onClick={() => fileInputRef.current?.click()}
          >
            browse
          </button>
        </p>
        
        <p className="mt-1 text-xs text-gray-500">
          PDF, DOC, DOCX or TXT up to 50MB
        </p>
      </div>

      {/* File List */}
      {selectedFiles.length > 0 && (
        <div className="mt-4 space-y-3">
          {selectedFiles.map((fileStatus) => (
            <div
              key={fileStatus.file.name}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div className="flex items-center space-x-3">
                <File className="h-5 w-5 text-gray-400" />
                <div>
                  <p className="text-sm font-medium text-gray-900">{fileStatus.file.name}</p>
                  <p className="text-xs text-gray-500">
                    {(fileStatus.file.size / (1024 * 1024)).toFixed(2)} MB
                  </p>
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                {fileStatus.status === 'pending' && (
                  <button
                    onClick={() => removeFile(fileStatus.file)}
                    className="text-gray-400 hover:text-gray-500"
                  >
                    <X className="h-5 w-5" />
                  </button>
                )}
                
                {fileStatus.status === 'uploading' && (
                  <Clock className="h-5 w-5 text-teal-500 animate-spin" />
                )}
                
                {fileStatus.status === 'complete' && (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                )}
                
                {fileStatus.status === 'error' && (
                  <div className="flex items-center space-x-1 text-red-500">
                    <AlertCircle className="h-5 w-5" />
                    <span className="text-xs">{fileStatus.error}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-lg flex items-center">
          <AlertCircle className="h-5 w-5 mr-2" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      {/* Upload Button */}
      {selectedFiles.length > 0 && (
        <div className="mt-4 flex justify-end space-x-3">
          <button
            onClick={resetUpload}
            className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-800"
            disabled={isUploading}
          >
            Cancel
          </button>
          <button
            onClick={handleUpload}
            disabled={isUploading || selectedFiles.every(f => f.status === 'complete')}
            className={`px-4 py-2 rounded-md text-sm font-medium text-white ${
              isUploading
                ? 'bg-teal-400 cursor-not-allowed'
                : 'bg-teal-600 hover:bg-teal-700'
            }`}
          >
            {isUploading ? 'Uploading...' : 'Upload Files'}
          </button>
        </div>
      )}
    </Card>
  )
} 