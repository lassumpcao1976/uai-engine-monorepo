'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { AuthModal } from '@/components/auth/AuthModal'

export default function Home() {
  const [showModal, setShowModal] = useState(false)
  const [modalMode, setModalMode] = useState<'signin' | 'signup'>('signin')

  return (
    <>
      <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-gray-900 via-purple-900 to-gray-900 relative overflow-hidden">
        {/* Animated background effects */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
        </div>

        <div className="relative z-10 max-w-2xl mx-auto text-center px-4">
          <h1 className="text-6xl font-bold mb-4 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent drop-shadow-2xl">
            UAI Engine
          </h1>
          <p className="text-2xl text-gray-300 mb-8 drop-shadow-lg">You think, we build.</p>
          <div className="flex gap-4 justify-center">
            <Button
              size="lg"
              onClick={() => {
                setModalMode('signup')
                setShowModal(true)
              }}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-lg shadow-purple-500/25"
            >
              Get Started
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={() => {
                setModalMode('signin')
                setShowModal(true)
              }}
              className="border-white/20 bg-white/5 text-white hover:bg-white/10 backdrop-blur-sm"
            >
              Sign In
            </Button>
          </div>
        </div>
      </div>

      {showModal && (
        <AuthModal
          initialMode={modalMode}
          isOverlay={true}
          onClose={() => setShowModal(false)}
        />
      )}
    </>
  )
}
