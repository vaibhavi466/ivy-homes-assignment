export interface Listing {
  listing_id: string

  is_live: boolean

  price: number

  locality: string | null

  property_type: string | null

  bedroom: number | null

  furnishing: string | null

  carpet_area: number | null

  super_built_up_area: number | null

  posted_at: string

  project_id: string | null

  website: string

  [key: string]: unknown
}
