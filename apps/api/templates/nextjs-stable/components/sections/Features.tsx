export function Features() {
  return (
    <section className="py-20 bg-gray-50">
      <div className="container mx-auto px-4">
        <h2 className="text-3xl font-bold text-center mb-12">Features</h2>
        <div className="grid md:grid-cols-3 gap-8">
          <div className="text-center">
            <h3 className="text-xl font-semibold mb-2">Feature One</h3>
            <p className="text-gray-600">Description of feature one</p>
          </div>
          <div className="text-center">
            <h3 className="text-xl font-semibold mb-2">Feature Two</h3>
            <p className="text-gray-600">Description of feature two</p>
          </div>
          <div className="text-center">
            <h3 className="text-xl font-semibold mb-2">Feature Three</h3>
            <p className="text-gray-600">Description of feature three</p>
          </div>
        </div>
      </div>
    </section>
  )
}
