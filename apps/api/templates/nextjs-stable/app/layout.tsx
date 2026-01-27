import type { Metadata } from 'next'
import './globals.css'
import { Header } from '@/components/layout/Header'
import { Footer } from '@/components/layout/Footer'
import { Watermark } from '@/components/Watermark'

export const metadata: Metadata = {
  title: '{{PROJECT_NAME}}',
  description: '{{PROJECT_DESCRIPTION}}',
  openGraph: {
    title: '{{PROJECT_NAME}}',
    description: '{{PROJECT_DESCRIPTION}}',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const showWatermark = process.env.NEXT_PUBLIC_SHOW_WATERMARK === 'true'
  
  return (
    <html lang="en">
      <body>
        <Header />
        <main>{children}</main>
        <Footer />
        {showWatermark && <Watermark />}
      </body>
    </html>
  )
}
