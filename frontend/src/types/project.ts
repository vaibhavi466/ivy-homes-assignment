export interface Project {
  project_id: string
  project_url: string

  city_id: number

  apartment_name: string
  developer_name: string | null

  locality: string | null
  project_status: string | null

  total_units: number | null
  total_towers: number | null
  total_floors: number | null

  launch_date: string | null
  possession_date: string | null

  rera_number: string | null

  min_area_sqft: number | null
  max_area_sqft: number | null

  amenities: string[]

  latitude: number | null
  longitude: number | null

  total_listings: number

  price_min: number | null
  price_max: number | null

  [key: string]: unknown
}
