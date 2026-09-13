import {
  formatArea,
  formatPrice,
} from './listing'

export function formatMonthlyRent(
  price: number,
) {
  return `${formatPrice(price)} / month`
}

export function formatRentalArea(
  area: number | null,
) {
  return formatArea(area)
}

export function formatRentalMoney(
  value: number | null,
) {
  if (
    value === null ||
    value === 0
  ) {
    return 'Not specified'
  }

  return formatPrice(value)
}

export function formatRentalPostedAt(
  postedAt: string,
) {
  const date = new Date(postedAt)

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return postedAt
  }

  return new Intl.DateTimeFormat(
    'en-IN',
    {
      dateStyle: 'medium',
      timeStyle: 'short',
    },
  ).format(date)
}
