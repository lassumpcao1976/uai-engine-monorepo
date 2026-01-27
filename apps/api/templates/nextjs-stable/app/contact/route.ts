import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { name, email, message } = body

    // TODO: Configure email provider (SendGrid, Resend, etc.)
    // For now, just log the contact form submission
    console.log('Contact form submission:', { name, email, message })

    return NextResponse.json({ success: true, message: 'Message sent successfully' })
  } catch (error) {
    return NextResponse.json(
      { success: false, error: 'Failed to send message' },
      { status: 500 }
    )
  }
}
