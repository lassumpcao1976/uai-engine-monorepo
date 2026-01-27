'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Project {
  id: string
  name: string
  status: string
  preview_url?: string
  latest_build?: {
    status: string
  }
}

interface User {
  id: string
  email: string
  credits: number
}

export default function Dashboard() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/')
      return
    }

    fetchUser()
    fetchProjects()
  }, [])

  const fetchUser = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (response.ok) {
        const data = await response.json()
        setUser(data)
      }
    } catch (err) {
      console.error('Failed to fetch user:', err)
    }
  }

  const fetchProjects = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`${API_URL}/projects`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (response.ok) {
        const data = await response.json()
        setProjects(data.projects || [])
      } else {
        setError('Failed to load projects')
      }
    } catch (err) {
      setError('Failed to load projects')
    } finally {
      setLoading(false)
    }
  }

  const handleSignOut = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    router.push('/')
  }

  if (loading) {
    return <div className="p-8">Loading...</div>
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold">UAI Engine</h1>
          <div className="flex items-center gap-4">
            {user && (
              <div className="text-sm">
                <span className="text-gray-600">Credits: </span>
                <span className="font-semibold">{user.credits.toFixed(2)}</span>
              </div>
            )}
            <button
              onClick={handleSignOut}
              className="text-sm text-gray-600 hover:text-gray-800"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-6 flex justify-between items-center">
          <h2 className="text-2xl font-semibold">Projects</h2>
          <Link
            href="/workspace/new"
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Create Project
          </Link>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {projects.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600 mb-4">No projects yet</p>
            <Link
              href="/workspace/new"
              className="text-blue-600 hover:text-blue-800"
            >
              Create your first project
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((project) => (
              <Link
                key={project.id}
                href={`/workspace/${project.id}`}
                className="bg-white border rounded-lg p-6 hover:shadow-md transition"
              >
                <h3 className="text-lg font-semibold mb-2">{project.name}</h3>
                <div className="flex items-center gap-2 text-sm">
                  <span
                    className={`px-2 py-1 rounded ${
                      project.status === 'ready'
                        ? 'bg-green-100 text-green-800'
                        : project.status === 'building'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {project.status}
                  </span>
                  {project.latest_build && (
                    <span className="text-gray-600">
                      Build: {project.latest_build.status}
                    </span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
