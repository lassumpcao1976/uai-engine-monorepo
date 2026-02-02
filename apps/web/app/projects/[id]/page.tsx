'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface Version {
  id: number
  prompt: string
  file_tree: any
  unified_diff: string | null
  created_at: string
}

interface Build {
  id: number
  status: string
  preview_url: string | null
  logs: string | null
  error_message: string | null
  created_at: string
}

export default function ProjectPage() {
  const router = useRouter()
  const params = useParams()
  const projectId = parseInt(params.id as string)
  const queryClient = useQueryClient()
  const [prompt, setPrompt] = useState('')
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null)
  const [selectedBuild, setSelectedBuild] = useState<number | null>(null)

  const { data: project } = useQuery({
    queryKey: ['project', projectId],
    queryFn: async () => {
      const res = await api.get(`/projects/${projectId}`)
      return res.data
    },
  })

  const { data: versions } = useQuery<Version[]>({
    queryKey: ['versions', projectId],
    queryFn: async () => {
      const res = await api.get(`/versions/projects/${projectId}/versions`)
      return res.data
    },
  })

  const { data: builds } = useQuery<Build[]>({
    queryKey: ['builds', projectId],
    queryFn: async () => {
      const res = await api.get(`/builds/projects/${projectId}/builds`)
      return res.data
    },
    refetchInterval: (query) => {
      const builds = query.state.data || []
      const hasRunning = builds.some((b: Build) => b.status === 'running' || b.status === 'pending')
      return hasRunning ? 5000 : false // Poll every 5 seconds if builds are running
    },
  })

  const createVersionMutation = useMutation({
    mutationFn: async (prompt: string) => {
      const res = await api.post(`/versions/projects/${projectId}/versions`, { prompt })
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['versions', projectId] })
      setPrompt('')
    },
  })

  const createBuildMutation = useMutation({
    mutationFn: async (versionId: number) => {
      const res = await api.post(`/builds/versions/${versionId}/builds`)
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['builds', projectId] })
    },
  })

  const handleCreateVersion = () => {
    if (prompt.trim()) {
      createVersionMutation.mutate(prompt)
    }
  }

  const handleCreateBuild = (versionId: number) => {
    createBuildMutation.mutate(versionId)
  }

  const currentBuild = builds?.find((b) => b.id === selectedBuild)

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <Button variant="ghost" onClick={() => router.push('/dashboard')}>
              ← Back to Dashboard
            </Button>
            <h1 className="text-xl font-bold">{project?.name || 'Project'}</h1>
            <div></div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Prompt Input & Versions */}
          <div className="lg:col-span-1 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Create Version</CardTitle>
                <CardDescription>Describe what you want to build</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="e.g., Create a modern landing page for a SaaS product with hero section, features, and pricing..."
                  className="w-full px-3 py-2 border rounded-md min-h-[150px]"
                />
                <Button
                  onClick={handleCreateVersion}
                  disabled={!prompt.trim() || createVersionMutation.isPending}
                  className="w-full"
                >
                  {createVersionMutation.isPending ? 'Generating...' : 'Generate Version'}
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Versions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {versions?.map((version) => (
                    <div
                      key={version.id}
                      className={`p-3 border rounded cursor-pointer ${
                        selectedVersion === version.id ? 'border-blue-500 bg-blue-50' : ''
                      }`}
                      onClick={() => setSelectedVersion(version.id)}
                    >
                      <p className="text-sm font-medium truncate">{version.prompt}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(version.created_at).toLocaleString()}
                      </p>
                      <Button
                        size="sm"
                        className="mt-2 w-full"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleCreateBuild(version.id)
                        }}
                        disabled={createBuildMutation.isPending}
                      >
                        Build
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column: File Tree, Diffs, Builds, Preview */}
          <div className="lg:col-span-2 space-y-6">
            {selectedVersion && (
              <>
                <Card>
                  <CardHeader>
                    <CardTitle>File Tree</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <pre className="text-xs bg-gray-100 p-4 rounded overflow-auto max-h-64">
                      {JSON.stringify(
                        versions?.find((v) => v.id === selectedVersion)?.file_tree,
                        null,
                        2
                      )}
                    </pre>
                  </CardContent>
                </Card>

                {versions?.find((v) => v.id === selectedVersion)?.unified_diff && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Unified Diff</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <pre className="text-xs bg-gray-100 p-4 rounded overflow-auto max-h-64">
                        {versions?.find((v) => v.id === selectedVersion)?.unified_diff}
                      </pre>
                    </CardContent>
                  </Card>
                )}
              </>
            )}

            <Card>
              <CardHeader>
                <CardTitle>Builds</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {builds?.map((build) => (
                    <div
                      key={build.id}
                      className={`p-3 border rounded cursor-pointer ${
                        selectedBuild === build.id ? 'border-blue-500 bg-blue-50' : ''
                      }`}
                      onClick={() => setSelectedBuild(build.id)}
                    >
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium">Build #{build.id}</span>
                        <span
                          className={`text-xs px-2 py-1 rounded ${
                            build.status === 'success'
                              ? 'bg-green-100 text-green-800'
                              : build.status === 'failed'
                              ? 'bg-red-100 text-red-800'
                              : build.status === 'running'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {build.status}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(build.created_at).toLocaleString()}
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {currentBuild && (
              <>
                {currentBuild.logs && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Build Logs</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <pre className="text-xs bg-gray-900 text-green-400 p-4 rounded overflow-auto max-h-64">
                        {currentBuild.logs}
                      </pre>
                    </CardContent>
                  </Card>
                )}

                {currentBuild.preview_url && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Preview</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <iframe
                        src={currentBuild.preview_url}
                        className="w-full h-[600px] border rounded"
                        title="Preview"
                      />
                    </CardContent>
                  </Card>
                )}

                {currentBuild.error_message && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Error</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <pre className="text-xs bg-red-50 text-red-800 p-4 rounded overflow-auto">
                        {currentBuild.error_message}
                      </pre>
                    </CardContent>
                  </Card>
                )}
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
