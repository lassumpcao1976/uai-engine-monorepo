'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { api } from '@/lib/api'

interface AuthModalProps {
  initialMode?: 'signin' | 'signup'
  onClose?: () => void
  isOverlay?: boolean
}

export function AuthModal({ initialMode = 'signin', onClose, isOverlay = false }: AuthModalProps) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [mode, setMode] = useState<'signin' | 'signup'>(initialMode)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  // Update mode when initialMode prop changes
  useEffect(() => {
    setMode(initialMode)
  }, [initialMode])

  useEffect(() => {
    const m = searchParams.get('message') || ''
    if (m) {
      setMessage(m)
    } else if (searchParams.get('registered') === 'true') {
      setMessage('Registration successful! Please sign in.')
      setMode('signin')
    }
  }, [searchParams])

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setMessage('')
    setLoading(true)

    try {
      const response = await api.post('/auth/login', {
        email,
        password,
      })
      localStorage.setItem('token', response.data.access_token)
      if (onClose) {
        onClose()
      } else {
        router.push('/dashboard')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setMessage('')
    setLoading(true)

    try {
      await api.post('/auth/register', {
        email,
        password,
        full_name: fullName,
      })
      if (isOverlay) {
        // In overlay mode, switch to signin mode
        setMessage('Registration successful! Please sign in.')
        setMode('signin')
        setEmail('')
        setPassword('')
        setFullName('')
      } else {
        // On dedicated page, redirect to signin
        router.push('/signin?registered=true')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = mode === 'signin' ? handleSignIn : handleSignUp

  return (
    <div
      className={`${
        isOverlay
          ? 'fixed inset-0 z-50 flex items-center justify-center p-6'
          : 'min-h-screen flex items-center justify-center p-6'
      }`}
    >
      {isOverlay && (
        <div
          className="absolute inset-0 bg-black/50 backdrop-blur-sm"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      <div className="relative w-full max-w-md rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl p-6 shadow-2xl shadow-purple-500/10">
        {/* Subtle glow effect */}
        <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-blue-500/10 via-purple-500/10 to-pink-500/10 opacity-50 blur-xl -z-10" />

        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-semibold text-white">
            {mode === 'signin' ? 'Sign in' : 'Create an account'}
          </h1>
          {isOverlay && onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
              aria-label="Close"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          )}
        </div>

        {message && (
          <div className="mb-4 rounded-lg border border-blue-400/30 bg-blue-500/10 backdrop-blur-sm p-3 text-sm text-blue-200">
            {message}
          </div>
        )}

        {error && (
          <div className="mb-4 rounded-lg border border-red-400/30 bg-red-500/10 backdrop-blur-sm p-3 text-sm text-red-200">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'signup' && (
            <div>
              <label htmlFor="fullName" className="block text-sm font-medium mb-2 text-gray-300">
                Full Name
              </label>
              <input
                id="fullName"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-4 py-2.5 rounded-lg border border-white/10 bg-white/5 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-transparent transition-all"
                placeholder="John Doe"
                required
                disabled={loading}
              />
            </div>
          )}
          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-2 text-gray-300">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg border border-white/10 bg-white/5 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-transparent transition-all"
              placeholder="you@example.com"
              autoComplete="email"
              required
              disabled={loading}
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium mb-2 text-gray-300">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg border border-white/10 bg-white/5 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-transparent transition-all"
              placeholder="Your password"
              autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
              required
              minLength={mode === 'signup' ? 8 : undefined}
              disabled={loading}
            />
          </div>
          <button
            type="submit"
            className="w-full rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 px-4 py-2.5 text-white font-medium hover:from-blue-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:ring-offset-2 focus:ring-offset-transparent transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-purple-500/25"
            disabled={loading}
          >
            {loading
              ? mode === 'signin'
                ? 'Signing in...'
                : 'Creating account...'
              : mode === 'signin'
              ? 'Sign in'
              : 'Sign up'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            type="button"
            onClick={() => {
              setMode(mode === 'signin' ? 'signup' : 'signin')
              setError('')
              setMessage('')
            }}
            className="text-sm text-gray-400 hover:text-white transition-colors"
          >
            {mode === 'signin' ? (
              <>
                Don't have an account?{' '}
                <span className="text-purple-400 font-medium">Sign up</span>
              </>
            ) : (
              <>
                Already have an account?{' '}
                <span className="text-purple-400 font-medium">Sign in</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
