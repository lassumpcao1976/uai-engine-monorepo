import { Metadata } from 'next'

export function generateMetadata(
  title: string,
  description: string,
  image?: string
): Metadata {
  return {
    title,
    description,
    openGraph: {
      title,
      description,
      images: image ? [image] : [],
      type: 'website',
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
      images: image ? [image] : [],
    },
  }
}
