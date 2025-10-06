'use client'

import React, { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Search, File, AlertCircle, CheckCircle } from 'lucide-react'

interface DocumentSearchResult {
  document_id: string
  text: string
  filename: string
  similarity_score: number
  metadata: {
    filename: string
    file_size: number
    content_type: string
    chunk_length: number
    total_chunks: number
    uploaded_at: string
  }
}

interface SearchResponse {
  success: boolean
  query: string
  results: DocumentSearchResult[]
  total_results: number
}

interface DocumentManagerProps {
  className?: string
  onSearchResult?: (results: DocumentSearchResult[]) => void
}

export default function DocumentManager({ 
  className = "",
  onSearchResult
}: DocumentManagerProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<DocumentSearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  const [hasSearched, setHasSearched] = useState(false)

  // Search documents
  const searchDocuments = async (query: string) => {
    if (!query.trim()) {
      setSearchResults([])
      setHasSearched(false)
      return
    }

    setIsSearching(true)
    setSearchError(null)

    try {
      // Get API URL from environment
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
      const searchUrl = `${apiBaseUrl}/search-documents`

      // Get auth token
      const token = localStorage.getItem('token')
      if (!token) {
        throw new Error('Authentication required')
      }

      const formData = new FormData()
      formData.append('query', query)
      formData.append('limit', '10')

      const response = await fetch(searchUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Search failed with status ${response.status}`)
      }

      const result: SearchResponse = await response.json()
      setSearchResults(result.results)
      setHasSearched(true)
      onSearchResult?.(result.results)

    } catch (error) {
      console.error('Search error:', error)
      const errorMessage = error instanceof Error ? error.message : 'Search failed'
      setSearchError(errorMessage)
      setSearchResults([])
      setHasSearched(true)
    } finally {
      setIsSearching(false)
    }
  }

  // Handle search input
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    searchDocuments(searchQuery)
  }

  // Get unique documents from search results
  const getUniqueDocuments = (results: DocumentSearchResult[]) => {
    const uniqueDocuments = new Map<string, DocumentSearchResult>()
    
    results.forEach(result => {
      const existing = uniqueDocuments.get(result.document_id)
      if (!existing || result.similarity_score < existing.similarity_score) {
        uniqueDocuments.set(result.document_id, result)
      }
    })
    
    return Array.from(uniqueDocuments.values())
  }

  const uniqueDocuments = getUniqueDocuments(searchResults)

  return (
    <Card className={`p-4 ${className}`}>
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-teal-800 mb-2">
            Search Your Documents
          </h3>
          <p className="text-sm text-gray-600">
            Search through your uploaded Medicare and insurance documents
          </p>
        </div>

        {/* Search Form */}
        <form onSubmit={handleSearchSubmit} className="flex space-x-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search your documents..."
            className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
            disabled={isSearching}
          />
          <Button
            type="submit"
            disabled={isSearching || !searchQuery.trim()}
            className="bg-teal-700 hover:bg-teal-800 text-white px-6"
          >
            {isSearching ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                Searching...
              </>
            ) : (
              <>
                <Search className="h-4 w-4 mr-2" />
                Search
              </>
            )}
          </Button>
        </form>

        {/* Search Results */}
        {hasSearched && (
          <div className="space-y-3">
            {searchError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start space-x-3">
                  <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-red-800">Search Error</p>
                    <p className="text-sm text-red-700 mt-1">{searchError}</p>
                  </div>
                </div>
              </div>
            )}

            {!searchError && searchResults.length === 0 && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <div className="flex items-start space-x-3">
                  <Search className="h-5 w-5 text-gray-500 mt-0.5" />
                  <div>
                    <p className="font-medium text-gray-700">No Results Found</p>
                    <p className="text-sm text-gray-600 mt-1">
                      No documents found matching &quot;{searchQuery}&quot;. Try different keywords or upload some documents first.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {uniqueDocuments.length > 0 && (
              <div>
                <h4 className="font-medium text-teal-800 mb-3">
                  Found {searchResults.length} matches in {uniqueDocuments.length} documents
                </h4>
                <div className="space-y-3">
                  {uniqueDocuments.map((doc) => {
                    const relatedResults = searchResults.filter(r => r.document_id === doc.document_id)
                    const uploadDate = new Date(doc.metadata.uploaded_at).toLocaleDateString()
                    
                    return (
                      <Card key={doc.document_id} className="p-4 bg-teal-50 border-teal-200">
                        <div className="space-y-2">
                          <div className="flex items-start justify-between">
                            <div className="flex items-start space-x-3">
                              <File className="h-5 w-5 text-teal-600 mt-0.5" />
                              <div className="flex-1">
                                <h5 className="font-medium text-teal-800">
                                  {doc.filename}
                                </h5>
                                <div className="text-xs text-teal-600 space-y-1 mt-1">
                                  <p>• Document ID: {doc.document_id}</p>
                                  <p>• Uploaded: {uploadDate}</p>
                                  <p>• Size: {(doc.metadata.file_size / 1024).toFixed(1)} KB</p>
                                  <p>• {relatedResults.length} relevant sections found</p>
                                </div>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-xs text-teal-700 font-medium">
                                Best Match: {(1 - doc.similarity_score).toFixed(1)}% relevant
                              </div>
                            </div>
                          </div>

                          {/* Top matching excerpts */}
                          <div className="bg-white rounded-lg p-3 border border-teal-200">
                            <p className="text-xs font-medium text-teal-700 mb-2">Most Relevant Excerpt:</p>
                            <p className="text-sm text-gray-700 leading-relaxed">
                              {doc.text.length > 200 ? `${doc.text.substring(0, 200)}...` : doc.text}
                            </p>
                          </div>
                        </div>
                      </Card>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Help Text */}
        {!hasSearched && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <CheckCircle className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <p className="font-medium text-blue-800">How to Search</p>
                <ul className="text-sm text-blue-700 mt-1 space-y-1">
                  <li>• Use natural language to search your documents</li>
                  <li>• Try queries like &quot;insurance coverage&quot; or &quot;prescription drugs&quot;</li>
                  <li>• Search results show the most relevant sections from your documents</li>
                  <li>• Upload documents first to enable search functionality</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  )
} 