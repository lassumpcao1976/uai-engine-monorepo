'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Build {
  id: string
  status: string
  build_logs?: string
  preview_url?: string
  error_message?: string
}

export default function PreviewPage() {
  const params = useParams()
  const projectId = params.projectId as string
  const buildId = params.buildId as string

  const [build, setBuild] = useState<Build | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchBuild()
  }, [projectId, buildId])

  const fetchBuild = async () => {
    try {
      const response = await fetch(`${API_URL}/projects/${projectId}/builds/${buildId}`)
      if (response.ok) {
        const data = await response.json()
        setBuild(data)
      }
    } catch (err) {
      console.error('Failed to fetch build:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div>Loading build information...</div>
      </div>
    )
  }

  if (!build) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div>Build not found</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold mb-4">Build Preview</h1>
        
        <div className="bg-white border rounded-lg p-6 mb-4">
          <div className="flex items-center gap-4 mb-4">
            <span
              className={`px-3 py-1 rounded ${
                build.status === 'success'
                  ? 'bg-green-100 text-green-800'
                  : build.status === 'failed'
                  ? 'bg-red-100 text-red-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}
            >
              {build.status}
            </span>
            <span className="text-sm text-gray-600">Build ID: {buildId}</span>
          </div>

          {build.status === 'success' && (
            <div className="mb-4">
              <p className="text-green-700 mb-2">✓ Build completed successfully</p>
              {build.preview_url && (
                <a
                  href={build.preview_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800"
                >
                  Open Preview →
                </a>
              )}
            </div>
          )}

          {build.status === 'failed' && build.error_message && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded">
              <p className="text-red-800 font-semibold mb-2">Build Failed</p>
              <p className="text-red-700 text-sm">{build.error_message}</p>
            </div>
          )}

          {build.build_logs && (
            <div className="mt-4">
              <h3 className="font-semibold mb-2">Build Logs</h3>
              <pre className="bg-gray-900 text-green-400 p-4 rounded text-xs overflow-auto max-h-96">
                {build.build_logs}
              </pre>
            </div>
          )}
        </div>

        <div className="text-center text-gray-600 text-sm">
          <p>This is a placeholder preview page.</p>
          <p>In production, this would serve the built Next.js application.</p>
        </div>
      </div>
    </div>
  )
}
