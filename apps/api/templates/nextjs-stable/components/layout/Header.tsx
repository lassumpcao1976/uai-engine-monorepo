import Link from 'next/link'

export function Header() {
  return (
    <header className="border-b">
      <nav className="container mx-auto px-4 py-4 flex justify-between items-center">
        <Link href="/" className="text-xl font-bold">
          {{PROJECT_NAME}}
        </Link>
        <div className="flex gap-6">
          <Link href="/" className="hover:text-blue-600">Home</Link>
          <Link href="/pricing" className="hover:text-blue-600">Pricing</Link>
          <Link href="/about" className="hover:text-blue-600">About</Link>
          <Link href="/contact" className="hover:text-blue-600">Contact</Link>
        </div>
      </nav>
    </header>
  )
}
