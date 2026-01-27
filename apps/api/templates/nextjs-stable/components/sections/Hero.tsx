export function Hero() {
  return (
    <section className="py-20 text-center">
      <div className="container mx-auto px-4">
        <h1 className="text-5xl font-bold mb-4">Welcome to {{PROJECT_NAME}}</h1>
        <p className="text-xl text-gray-600 mb-8">Build amazing things with us</p>
        <button className="bg-blue-600 text-white px-8 py-3 rounded hover:bg-blue-700">
          Get Started
        </button>
      </div>
    </section>
  )
}
