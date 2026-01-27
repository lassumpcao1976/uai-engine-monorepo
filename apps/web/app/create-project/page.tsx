'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { CheckCircle2, Circle, Download, FileText, BarChart3 } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type Step = 'plan' | 'generate' | 'package' | 'evaluate' | 'ready'

interface Project {
  id: string
  name: string
  prompt: string
  template_type: string
  status: string
}

export default function CreateProjectPage() {
  const router = useRouter()
  const [projectName, setProjectName] = useState('')
  const [prompt, setPrompt] = useState('')
  const [templateType, setTemplateType] = useState<string>('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [currentStep, setCurrentStep] = useState<Step | null>(null)
  const [projectId, setProjectId] = useState<string | null>(null)
  const [isReady, setIsReady] = useState(false)

  const steps: { key: Step; label: string }[] = [
    { key: 'plan', label: 'Plan' },
    { key: 'generate', label: 'Generate' },
    { key: 'package', label: 'Package' },
    { key: 'evaluate', label: 'Evaluate' },
    { key: 'ready', label: 'Ready' },
  ]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!projectName || !prompt || !templateType) return

    setIsSubmitting(true)
    setCurrentStep('plan')

    try {
      // Create project
      const createResponse = await fetch(`${API_URL}/api/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: projectName,
          prompt,
          template_type: templateType,
        }),
      })

      if (!createResponse.ok) throw new Error('Failed to create project')

      const project: Project = await createResponse.json()
      setProjectId(project.id)

      // Simulate progress
      const stepOrder: Step[] = ['plan', 'generate', 'package', 'evaluate', 'ready']
      for (let i = 0; i < stepOrder.length; i++) {
        setCurrentStep(stepOrder[i])
        await new Promise((resolve) => setTimeout(resolve, 1000))
      }

      // Generate project
      const generateResponse = await fetch(`${API_URL}/api/projects/${project.id}/generate`, {
        method: 'POST',
      })

      if (!generateResponse.ok) throw new Error('Failed to generate project')

      setIsReady(true)
    } catch (error) {
      console.error('Error:', error)
      alert('Failed to create project. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDownload = () => {
    if (projectId) {
      window.open(`${API_URL}/api/projects/${projectId}/artifact`, '_blank')
    }
  }

  const handleViewManifest = async () => {
    if (projectId) {
      const response = await fetch(`${API_URL}/api/projects/${projectId}/manifest`)
      const manifest = await response.json()
      const blob = new Blob([JSON.stringify(manifest, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'manifest.json'
      a.click()
    }
  }

  const handleViewEvaluation = async () => {
    if (projectId) {
      const response = await fetch(`${API_URL}/api/projects/${projectId}/evaluation`)
      const evaluation = await response.json()
      const blob = new Blob([JSON.stringify(evaluation, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'evaluation.json'
      a.click()
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Create Project</h1>
          <p className="text-gray-600">Generate a new project template</p>
        </div>

        {!isReady ? (
          <Card>
            <CardHeader>
              <CardTitle>Project Details</CardTitle>
              <CardDescription>Fill in the details to generate your project</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Project Name
                  </label>
                  <input
                    type="text"
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary focus:border-transparent"
                    placeholder="My Awesome Project"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Prompt
                  </label>
                  <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary focus:border-transparent min-h-[120px]"
                    placeholder="Describe what you want to build..."
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Template Type
                  </label>
                  <Select value={templateType} onValueChange={setTemplateType} required>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select a template type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="nextjs-saas">Next.js SaaS starter</SelectItem>
                      <SelectItem value="fastapi-api">FastAPI API starter</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Button type="submit" disabled={isSubmitting} className="w-full">
                  {isSubmitting ? 'Creating...' : 'Create Project'}
                </Button>
              </form>

              {currentStep && (
                <div className="mt-8">
                  <h3 className="text-lg font-semibold mb-4">Progress</h3>
                  <div className="space-y-3">
                    {steps.map((step, index) => {
                      const isActive = steps.findIndex((s) => s.key === currentStep) >= index
                      return (
                        <div key={step.key} className="flex items-center gap-3">
                          {isActive ? (
                            <CheckCircle2 className="h-5 w-5 text-green-500" />
                          ) : (
                            <Circle className="h-5 w-5 text-gray-300" />
                          )}
                          <span className={isActive ? 'text-gray-900' : 'text-gray-400'}>
                            {step.label}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>Project Ready!</CardTitle>
              <CardDescription>Your project has been generated successfully</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button onClick={handleDownload} className="w-full" size="lg">
                <Download className="mr-2 h-4 w-4" />
                Download Repo Zip
              </Button>
              <Button onClick={handleViewManifest} variant="outline" className="w-full">
                <FileText className="mr-2 h-4 w-4" />
                View Manifest
              </Button>
              <Button onClick={handleViewEvaluation} variant="outline" className="w-full">
                <BarChart3 className="mr-2 h-4 w-4" />
                View Evaluation Report
              </Button>
              <Button
                onClick={() => router.push('/dashboard')}
                variant="ghost"
                className="w-full"
              >
                Back to Dashboard
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
