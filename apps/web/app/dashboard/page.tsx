'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface Project {
  id: number
  name: string
  description: string | null
  created_at: string
}

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/signin')
      return
    }
    api.get('/auth/me').then((res) => setUser(res.data)).catch(() => router.push('/signin'))
  }, [router])

  const { data: projects, isLoading } = useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: async () => {
      const res = await api.get('/projects')
      return res.data
    },
  })

  const { data: credits } = useQuery({
    queryKey: ['credits'],
    queryFn: async () => {
      const res = await api.get('/credits/balance')
      return res.data
    },
  })

  const handleLogout = () => {
    localStorage.removeItem('token')
    router.push('/signin')
  }

  if (!user) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <Link href="/dashboard" className="text-xl font-bold">
              UAI Engine
            </Link>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">
                Credits: <span className="font-semibold">{credits?.credits || 0}</span>
              </span>
              <span className="text-sm text-gray-600">{user.email}</span>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                Logout
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">Projects</h1>
          <Link href="/projects/new">
            <Button>New Project</Button>
          </Link>
        </div>

        {isLoading ? (
          <div>Loading projects...</div>
        ) : projects && projects.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <Link key={project.id} href={`/projects/${project.id}`}>
                <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                  <CardHeader>
                    <CardTitle>{project.name}</CardTitle>
                    <CardDescription>
                      {project.description || 'No description'}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-500">
                      Created {new Date(project.created_at).toLocaleDateString()}
                    </p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-gray-500 mb-4">No projects yet</p>
              <Link href="/projects/new">
                <Button>Create your first project</Button>
              </Link>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  )
}
