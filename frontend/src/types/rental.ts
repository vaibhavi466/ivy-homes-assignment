export interface Rental {
  listing_id: string
  listing_url: string
  website: string

  city_id: number

  title: string
  apartment_name: string | null
  locality: string | null
  property_type: string | null

  bedroom: number | null
  bathroom: number | null

  floor: number | null
  total_floors: number | null

  furnishing: string | null
  facing_direction: string | null

  price: number
  deposit: number | null
  maintenance: number | null

  carpet_area: number | null
  super_builtup_area: number | null

  latitude: number | null
  longitude: number | null

  posted_by: string | null
  posted_by_name: string | null
  posted_by_contact: string | null

  description: string | null

  posted_at: string

  is_live: boolean

  [key: string]: unknown
}
