export default function ContactPage() {
  return (
    <div className="container mx-auto px-4 py-16">
      <h1 className="text-4xl font-bold text-center mb-8">Contact Us</h1>
      <form className="max-w-md mx-auto">
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">Name</label>
          <input type="text" className="w-full px-4 py-2 border rounded" />
        </div>
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">Email</label>
          <input type="email" className="w-full px-4 py-2 border rounded" />
        </div>
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">Message</label>
          <textarea className="w-full px-4 py-2 border rounded" rows={5} />
        </div>
        <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700">
          Send Message
        </button>
      </form>
    </div>
  )
}
