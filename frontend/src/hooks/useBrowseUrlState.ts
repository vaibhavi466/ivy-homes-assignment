import {
  useCallback,
  useMemo,
} from 'react'

import {
  useSearchParams,
} from 'react-router-dom'

type StringObject<T> = {
  [Key in keyof T]: string
}

interface BrowseUrlStateOptions<
  T extends StringObject<T>,
> {
  defaults: T

  paramNames: {
    [Key in keyof T]: string
  }

  validValues?: Partial<{
    [Key in keyof T]:
      readonly string[]
  }>
}

export function useBrowseUrlState<
  T extends StringObject<T>,
>({
  defaults,
  paramNames,
  validValues,
}: BrowseUrlStateOptions<T>) {
  const [
    searchParams,
    setSearchParams,
  ] = useSearchParams()

  const filters = useMemo(() => {
    const next = {
      ...defaults,
    }

    for (
      const key of Object.keys(
        defaults,
      ) as Array<keyof T>
    ) {
      const parameterName =
        paramNames[key]

      const value =
        searchParams.get(
          parameterName,
        )

      if (value === null) {
        continue
      }

      const allowedValues =
        validValues?.[key]

      if (
        allowedValues &&
        !allowedValues.includes(
          value,
        )
      ) {
        continue
      }

      next[key] =
        value as T[typeof key]
    }

    return next
  }, [
    defaults,
    paramNames,
    searchParams,
    validValues,
  ])

  const pageIndex = useMemo(() => {
    const rawPage =
      searchParams.get('page')

    if (!rawPage) {
      return 0
    }

    const page =
      Number(rawPage)

    if (
      !Number.isInteger(page) ||
      page < 1
    ) {
      return 0
    }

    return page - 1
  }, [searchParams])

  const updateFilter =
    useCallback(
      <
        Key extends keyof T,
      >(
        key: Key,
        value: T[Key],
      ) => {
        const next =
          new URLSearchParams(
            searchParams,
          )

        const parameterName =
          paramNames[key]

        if (
          value ===
            defaults[key] ||
          !value.trim()
        ) {
          next.delete(
            parameterName,
          )
        } else {
          next.set(
            parameterName,
            value,
          )
        }

        /*
         * Every filter change returns
         * browsing to page 1.
         */
        next.delete('page')

        setSearchParams(
          next,
          {
            replace: true,
          },
        )
      },
      [
        defaults,
        paramNames,
        searchParams,
        setSearchParams,
      ],
    )

  const clearFilters =
    useCallback(() => {
      setSearchParams(
        new URLSearchParams(),
        {
          replace: true,
        },
      )
    }, [setSearchParams])

  const goToPage =
    useCallback(
      (
        nextPageIndex: number,
      ) => {
        const next =
          new URLSearchParams(
            searchParams,
          )

        if (
          nextPageIndex <= 0
        ) {
          next.delete('page')
        } else {
          next.set(
            'page',
            String(
              nextPageIndex + 1,
            ),
          )
        }

        setSearchParams(next)
      },
      [
        searchParams,
        setSearchParams,
      ],
    )

  return {
    filters,
    pageIndex,
    updateFilter,
    clearFilters,
    goToPage,
  }
}
