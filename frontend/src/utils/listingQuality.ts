const CORRUPT_LISTING_IDS = new Set([
  '100-6000323',
  '100-6000338',
  '100-6001461',
  '100-6001968',
  '100-6002071',
  'DWE-6000010',
  'DWE-6001015',
  'DWE-6002663',
  'DWE-6002846',
  'MAG-6000453',
  'MAG-6000527',
  'MAG-6000631',
  'MAG-6001135',
  'MAG-6002834',
  'SQU-6001477',
  'SQU-6003044',
  'ZER-6000468',
  'ZER-6000669',
])

const FAKE_LISTING_IDS = new Set([
  '100-6000578',
  '100-6000678',
  '100-6001599',
  'MAG-6002472',
  'MAG-6002941',
  'SQU-6000395',
])

export function isCorruptListing(
  listingId: string,
) {
  return CORRUPT_LISTING_IDS.has(
    listingId,
  )
}

export function isFakeListing(
  listingId: string,
) {
  return FAKE_LISTING_IDS.has(
    listingId,
  )
}

export function isKnownUnreliableListing(
  listingId: string,
) {
  return (
    isCorruptListing(listingId) ||
    isFakeListing(listingId)
  )
}
