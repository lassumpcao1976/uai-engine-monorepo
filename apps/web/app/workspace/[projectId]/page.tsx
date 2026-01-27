'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import dynamic from 'next/dynamic'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Dynamically import Monaco editor (client-side only)
const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false })

interface Project {
  id: string
  name: string
  status: string
  preview_url?: string
  latest_build?: {
    status: string
    id: string
  }
}

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

interface FileNode {
  name: string
  path: string
  type: 'file' | 'directory'
  children?: FileNode[]
}

export default function Workspace() {
  const router = useRouter()
  const params = useParams()
  const projectId = params.projectId as string

  const [project, setProject] = useState<Project | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState<'files' | 'diff' | 'logs' | 'history'>('files')
  const [fileTree, setFileTree] = useState<FileNode[]>([])
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [fileContent, setFileContent] = useState('')
  const [buildLogs, setBuildLogs] = useState('')
  const [versions, setVersions] = useState<any[]>([])
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null)
  const [diffText, setDiffText] = useState<string>('')

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/')
      return
    }

    if (projectId === 'new') {
      // Handle new project creation
      return
    }

    fetchProject()
    fetchMessages()
    fetchFileTree()
  }, [projectId])

  const fetchProject = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`${API_URL}/projects/${projectId}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (response.ok) {
        const data = await response.json()
        setProject(data)
        if (data.latest_build) {
          setBuildLogs(data.latest_build.build_logs || '')
          // Set preview URL from latest build
          if (data.latest_build.preview_url) {
            setPreviewUrl(data.latest_build.preview_url)
          } else if (data.latest_build.status === 'success') {
            // Construct preview URL if build succeeded but preview_url not set
            setPreviewUrl(`${API_URL}/preview/${projectId}/${data.latest_build.id}`)
          } else {
            setPreviewUrl(null)
          }
        } else {
          setPreviewUrl(null)
        }
      } else {
        const errorData = await response.json()
        setError(errorData.error?.message || 'Failed to load project')
      }
    } catch (err) {
      console.error('Failed to fetch project:', err)
    }
  }

  const fetchMessages = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`${API_URL}/projects/${projectId}/messages`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (response.ok) {
        const data = await response.json()
        setMessages(data.messages.map((msg: any) => ({
          id: msg.id,
          role: msg.role,
          content: msg.content,
          created_at: msg.created_at
        })))
      }
    } catch (err) {
      console.error('Failed to fetch messages:', err)
    }
  }

  const fetchFileTree = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`${API_URL}/projects/${projectId}/files/tree`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (response.ok) {
        const data = await response.json()
        setFileTree(data)
      }
    } catch (err) {
      console.error('Failed to fetch file tree:', err)
    }
  }

  const fetchFileContent = async (path: string) => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(
        `${API_URL}/projects/${projectId}/files/content?path=${encodeURIComponent(path)}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      )
      if (response.ok) {
        const data = await response.json()
        setFileContent(data.content)
        setSelectedFile(path)
      }
    } catch (err) {
      console.error('Failed to fetch file content:', err)
    }
  }

  const fetchVersions = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`${API_URL}/projects/${projectId}/versions`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (response.ok) {
        const data = await response.json()
        setVersions(data)
        // If no version selected, select the latest
        if (!selectedVersionId && data.length > 0) {
          setSelectedVersionId(data[0].id)
          setDiffText(data[0].unified_diff_text || '')
        }
      }
    } catch (err) {
      console.error('Failed to fetch versions:', err)
    }
  }

  const fetchVersionDiff = async (versionId: string) => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`${API_URL}/projects/${projectId}/versions/${versionId}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (response.ok) {
        const data = await response.json()
        setDiffText(data.unified_diff_text || '')
      }
    } catch (err) {
      console.error('Failed to fetch version diff:', err)
    }
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      created_at: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`${API_URL}/projects/${projectId}/prompt`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: input }),
      })

      const data = await response.json()

      if (response.ok) {
        setError('') // Clear any previous errors
        
        // Add assistant response with credit info
        let content = `Version ${data.version.version_number} created. Build status: ${data.build.status}`
        if (data.credit_info) {
          content += `\n\nCredits: -${data.credit_info.charged_amount} (${data.credit_info.charged_action})`
          content += `\nBalance: ${data.credit_info.wallet_balance_after.toFixed(2)}`
          if (data.credit_info.transaction_id) {
            content += `\nTransaction: ${data.credit_info.transaction_id}`
          }
        }
        
        const assistantMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: content,
          created_at: new Date().toISOString(),
        }
        setMessages((prev) => [...prev, assistantMessage])

        // Update preview URL if build succeeded
        if (data.build.status === 'success' && data.build.preview_url) {
          setPreviewUrl(data.build.preview_url)
        } else if (data.build.status === 'success') {
          setPreviewUrl(`${API_URL}/preview/${projectId}/${data.build.id}`)
        }

        // Refresh project and file tree
        fetchProject()
        fetchFileTree()
      } else {
        const errorMsg = data.error?.message || data.error?.code || 'Failed to process prompt'
        setError(errorMsg)
        // Add error message to chat
        const errorMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `Error: ${errorMsg}`,
          created_at: new Date().toISOString(),
        }
        setMessages((prev) => [...prev, errorMessage])
      }
    } catch (err: any) {
      const errorMsg = err.message || 'An error occurred. Please try again.'
      setError(errorMsg)
      // Add error message to chat
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${errorMsg}`,
        created_at: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const renderFileTree = (nodes: FileNode[], level = 0) => {
    return (
      <div className="pl-4">
        {nodes.map((node) => (
          <div key={node.path}>
            <div
              className={`py-1 px-2 cursor-pointer hover:bg-gray-100 ${
                selectedFile === node.path ? 'bg-blue-50' : ''
              }`}
              style={{ paddingLeft: `${level * 16}px` }}
              onClick={() => {
                if (node.type === 'file') {
                  fetchFileContent(node.path)
                }
              }}
            >
              {node.type === 'directory' ? '📁' : '📄'} {node.name}
            </div>
            {node.children && renderFileTree(node.children, level + 1)}
          </div>
        ))}
      </div>
    )
  }

  if (projectId === 'new') {
    return <div>New project creation form (TODO)</div>
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <header className="bg-white border-b px-4 py-2 flex justify-between items-center">
        <div className="flex items-center gap-4">
          <button onClick={() => router.push('/dashboard')} className="text-gray-600">
            ← Back
          </button>
          <h1 className="text-lg font-semibold">{project?.name || 'Loading...'}</h1>
        </div>
        {previewUrl && (
          <a
            href={previewUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            View Preview
          </a>
        )}
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* Left: Chat Panel */}
        <div className="w-1/3 border-r bg-white flex flex-col">
          <div className="p-4 border-b">
            <h2 className="font-semibold mb-2">Chat</h2>
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded mb-2 text-sm">
                {error}
              </div>
            )}
            <form onSubmit={handleSendMessage} className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Describe changes..."
                className="flex-1 px-3 py-2 border rounded"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50"
              >
                Send
              </button>
            </form>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`p-2 rounded ${
                  msg.role === 'user' ? 'bg-blue-50 ml-8' : 'bg-gray-50 mr-8'
                }`}
              >
                <div className="text-xs text-gray-500 mb-1">{msg.role}</div>
                <div>{msg.content}</div>
              </div>
            ))}
            {loading && <div className="text-gray-500">Processing...</div>}
          </div>
        </div>

        {/* Center: Preview */}
        <div className="flex-1 bg-white">
          {previewUrl ? (
            <iframe
              src={previewUrl}
              className="w-full h-full border-0"
              title="Preview"
            />
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              {project?.latest_build?.status === 'failed' ? (
                <div className="text-center">
                  <div className="text-red-600 font-semibold mb-2">Build Failed</div>
                  <div className="text-sm">Check the Logs tab for details</div>
                </div>
              ) : (
                'No preview available. Build in progress or not started.'
              )}
            </div>
          )}
        </div>

        {/* Right: Tabs */}
        <div className="w-1/3 border-l bg-white flex flex-col">
          <div className="flex border-b">
            {['files', 'diff', 'logs', 'history'].map((tab) => (
              <button
                key={tab}
                onClick={() => {
                  setActiveTab(tab as any)
                  if (tab === 'history') fetchVersions()
                  if (tab === 'diff') {
                    fetchVersions()
                    if (versions.length > 0 && !selectedVersionId) {
                      setSelectedVersionId(versions[0].id)
                      setDiffText(versions[0].unified_diff_text || '')
                    }
                  }
                }}
                className={`flex-1 px-4 py-2 text-sm ${
                  activeTab === tab
                    ? 'border-b-2 border-blue-600 text-blue-600'
                    : 'text-gray-600'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            {activeTab === 'files' && (
              <div>
                {fileTree.length > 0 ? (
                  renderFileTree(fileTree)
                ) : (
                  <div className="text-gray-500">No files</div>
                )}
                {selectedFile && (
                  <div className="mt-4 border-t pt-4">
                    <div className="text-sm font-semibold mb-2">{selectedFile}</div>
                    <MonacoEditor
                      height="400px"
                      language="typescript"
                      value={fileContent}
                      options={{ readOnly: true }}
                    />
                  </div>
                )}
              </div>
            )}
            {activeTab === 'diff' && (
              <div>
                {versions.length > 0 ? (
                  <div>
                    <div className="mb-4">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Select Version:
                      </label>
                      <select
                        value={selectedVersionId || ''}
                        onChange={(e) => {
                          setSelectedVersionId(e.target.value)
                          if (e.target.value) {
                            fetchVersionDiff(e.target.value)
                          }
                        }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      >
                        {versions.map((v) => (
                          <option key={v.id} value={v.id}>
                            Version {v.version_number} - {new Date(v.created_at).toLocaleString()}
                          </option>
                        ))}
                      </select>
                    </div>
                    {diffText ? (
                      <pre className="text-xs bg-gray-900 p-4 rounded overflow-auto font-mono">
                        {diffText.split('\n').map((line, i) => {
                          let className = 'text-gray-300'
                          if (line.startsWith('+') && !line.startsWith('+++')) {
                            className = 'text-green-400'
                          } else if (line.startsWith('-') && !line.startsWith('---')) {
                            className = 'text-red-400'
                          } else if (line.startsWith('@@')) {
                            className = 'text-blue-400'
                          } else if (line.startsWith('+++') || line.startsWith('---')) {
                            className = 'text-yellow-400'
                          }
                          return (
                            <div key={i} className={className}>
                              {line}
                            </div>
                          )
                        })}
                      </pre>
                    ) : (
                      <div className="text-gray-500 text-center py-8">
                        No diff available for this version
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-gray-500 text-center py-8">
                    No versions available
                  </div>
                )}
              </div>
            )}
            {activeTab === 'logs' && (
              <div>
                <pre className="text-xs bg-gray-900 text-green-400 p-4 rounded overflow-auto">
                  {buildLogs || 'No logs available'}
                </pre>
              </div>
            )}
            {activeTab === 'history' && (
              <div>
                {versions.map((v) => (
                  <div key={v.id} className="border-b py-2">
                    <div className="font-semibold">Version {v.version_number}</div>
                    <div className="text-xs text-gray-500">
                      {new Date(v.created_at).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
