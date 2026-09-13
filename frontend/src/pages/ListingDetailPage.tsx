import { useParams } from 'react-router-dom'

export function ListingDetailPage() {
  const { id } = useParams()

  return <h1>Listing: {id}</h1>
}
