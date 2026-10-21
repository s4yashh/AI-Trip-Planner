import { bookingHotelUrl, type StayDetails } from "@/lib/booking-links";
import { safeWebsite } from "@/lib/live-api";
import type { HotelLabel, HotelSuggestion } from "@/types/hotels";
import type { Currency } from "@/types/live";

const LABEL_STYLES: Record<HotelLabel, string> = {
  "Cheapest": "bg-emerald-50 text-emerald-800 border-emerald-200",
  "Best rated": "bg-amber-50 text-amber-800 border-amber-200",
  "Best value": "bg-sky-50 text-sky-800 border-sky-200",
};

// Estimates are rounded, so whole-unit amounts read more honestly than paise or cents.
function approx(value: number, currency: Currency) {
  return new Intl.NumberFormat("en-IN", {style: "currency", currency, maximumFractionDigits: 0}).format(value);
}

function Estimate({basis}: {basis: HotelSuggestion["price_basis"]}) {
  if (basis === "ai_estimate") return <span className="source-tag source-estimated">AI estimate</span>;
  if (basis === "openstreetmap") return <span className="source-tag source-live">OpenStreetMap</span>;
  return null;
}

export function HotelCard({hotel, stay, currency, nights}: {
  hotel: HotelSuggestion; stay: StayDetails; currency: Currency; nights: number;
}) {
  const website = safeWebsite(hotel.website);
  const price = hotel.price_per_night == null ? null : Math.round(hotel.price_per_night);
  const location = [hotel.area, hotel.distance_km != null ? `${hotel.distance_km} km from centre` : null].filter(Boolean).join(" · ");
  return <article className="place-card flex flex-col">
    <div className="flex flex-wrap gap-1.5">
      {hotel.labels.map(label => <span key={label} className={`rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${LABEL_STYLES[label]}`}>{label}</span>)}
      {!hotel.verified_listing && <span className="source-tag source-estimated">Unverified AI suggestion</span>}
    </div>
    <h3>{hotel.name}</h3>
    <p>{location || "Area not listed"}</p>

    <div className="mt-4 flex flex-wrap items-end justify-between gap-3 border-t border-[#edf0e8] pt-4">
      <div>
        {price != null ? <>
          <strong className="font-display text-2xl">≈ {approx(price, currency)}</strong><span className="text-xs text-slate-500"> / night</span>
          <p className="mt-1 text-[11px] text-slate-500">Approx. {approx(price * nights * stay.rooms, currency)} for {nights} night{nights === 1 ? "" : "s"}, {stay.rooms} room{stay.rooms === 1 ? "" : "s"}</p>
        </> : <p className="text-sm text-slate-600">Price: check on the booking site</p>}
      </div>
      <Estimate basis={hotel.price_basis}/>
    </div>

    <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
      {hotel.rating == null ? <span className="text-slate-500">Rating not available</span>
        : hotel.rating_basis === "openstreetmap"
          ? <span><span aria-hidden="true" className="text-amber-500">★</span> {hotel.rating}-star hotel class</span>
          : <span><span aria-hidden="true" className="text-amber-500">★</span> {hotel.rating.toFixed(1)} / 5 guest rating</span>}
      <Estimate basis={hotel.rating_basis}/>
    </div>

    {hotel.amenities.length > 0 && <div className="mt-3">
      <ul className="flex flex-wrap gap-1.5" aria-label="Key amenities">
        {hotel.amenities.map(amenity => <li key={amenity} className="rounded-md bg-[#f3f5ed] px-2 py-1 text-[11px] text-[#5d6f58]">{amenity}</li>)}
      </ul>
      {hotel.amenities_basis === "ai_estimate" && <p className="mt-1.5 text-[10px] text-slate-500">Likely amenities (AI estimate). Confirm before booking.</p>}
    </div>}

    <div className="mt-auto flex flex-wrap items-center gap-3 pt-5">
      <a className="primary-btn" href={bookingHotelUrl(stay, hotel.name)} target="_blank" rel="noopener noreferrer">
        Book now<span aria-hidden="true">↗</span><span className="sr-only"> (opens Booking.com in a new tab)</span>
      </a>
      {website && <a className="text-xs text-[#3e7659] underline-offset-2 hover:underline" href={website} target="_blank" rel="noopener noreferrer">Hotel website</a>}
    </div>
  </article>;
}
