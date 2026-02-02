'use client'

import { Suspense } from 'react'
import { AuthModal } from '@/components/auth/AuthModal'

function SignInPageContent() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-gray-900 via-purple-900 to-gray-900 relative overflow-hidden">
      {/* Animated background effects */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
      </div>

      <AuthModal initialMode="signin" isOverlay={false} />
    </div>
  )
}

export default function Page() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-gray-900 via-purple-900 to-gray-900 text-white">Loading...</div>}>
      <SignInPageContent />
    </Suspense>
  )
}
