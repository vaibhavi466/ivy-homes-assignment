import type { Listing } from '../types/listing'
import {
  getListingConfidence,
  type ConfidenceLevel,
} from '../utils/listingConfidence'

interface ListingConfidencePanelProps {
  listing: Listing
}

function getLevelLabel(
  level: ConfidenceLevel,
) {
  switch (level) {
    case 'verified':
      return 'Verified'

    case 'normalized':
      return 'Normalized'

    case 'warning':
      return 'Warning'
  }
}

export function ListingConfidencePanel({
  listing,
}: ListingConfidencePanelProps) {
  const confidence =
    getListingConfidence(listing)

  return (
    <section
      className="confidence-panel"
      aria-labelledby="confidence-title"
    >
      <div className="confidence-header">
        <div>
          <p className="page-eyebrow">
            Data confidence
          </p>

          <h2 id="confidence-title">
            What we verified
          </h2>

          <p className="confidence-description">
            These checks explain how this
            listing is interpreted before it
            is shown or used in market
            calculations.
          </p>
        </div>

        <span
          className={
            confidence.hasWarning
              ? 'confidence-summary warning'
              : 'confidence-summary verified'
          }
        >
          {confidence.hasWarning
            ? 'Review recommended'
            : 'Checks passed'}
        </span>
      </div>

      <div className="confidence-list">
        {confidence.items.map(
          (item) => (
            <article
              key={item.title}
              className={`confidence-item confidence-${item.level}`}
            >
              <div className="confidence-item-heading">
                <span
                  className="confidence-indicator"
                  aria-hidden="true"
                >
                  {item.level === 'verified'
                    ? '✓'
                    : item.level ===
                        'normalized'
                      ? '↻'
                      : '!'}
                </span>

                <div>
                  <div className="confidence-title-row">
                    <h3>
                      {item.title}
                    </h3>

                    <span className="confidence-label">
                      {getLevelLabel(
                        item.level,
                      )}
                    </span>
                  </div>

                  <p>
                    {item.description}
                  </p>
                </div>
              </div>
            </article>
          ),
        )}
      </div>
    </section>
  )
}
