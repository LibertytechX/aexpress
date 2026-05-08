'use client';

import { useEffect, useRef, useState } from 'react';

declare global {
  interface Window {
    google: any;
    googleMapsLoaded?: boolean;
  }
}

/* ─── Lagos Bounds ──────────────────────────────────────────────── */
const LAGOS_CENTER = { lat: 6.5244, lng: 3.3792 };
const LAGOS_BOUNDS = { minLat: 6.25, maxLat: 6.75, minLng: 2.70, maxLng: 3.95 };
const isInLagos = (lat: number, lng: number) =>
  lat >= LAGOS_BOUNDS.minLat && lat <= LAGOS_BOUNDS.maxLat &&
  lng >= LAGOS_BOUNDS.minLng && lng <= LAGOS_BOUNDS.maxLng;
const REVERSE_GEOCODE_MIN_DELTA = 0.00015;
const reverseGeocodeCacheKey = (lat: number, lng: number) => `${lat.toFixed(5)},${lng.toFixed(5)}`;
const hasMeaningfulCenterChange = (
  previous: { lat: number; lng: number } | null,
  next: { lat: number; lng: number }
) => !previous ||
Math.abs(previous.lat - next.lat) > REVERSE_GEOCODE_MIN_DELTA ||
  Math.abs(previous.lng - next.lng) > REVERSE_GEOCODE_MIN_DELTA;

interface MapPickerModalProps {
  /** Called when user confirms a location. Receives the resolved address string and coordinates. */
  onConfirm: (address: string, lat: number, lng: number) => void;
  /** Called when the user dismisses without picking. */
  onClose: () => void;
}

/* ─── MapPickerModal ─────────────────────────────────────────────
   Full-screen Google Maps modal.
   - A fixed crosshair pin sits centered on the map container while
     the user drags the map underneath it.
   - A debounced reverse-geocode fires after the map stops moving and
     shows the resolved address in a bottom confirmation bar.
   - "Use this address" confirms; "Cancel" closes without saving.
──────────────────────────────────────────────────────────────── */
export default function MapPickerModal({ onConfirm, onClose }: MapPickerModalProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const geocoderRef = useRef<any>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [resolvedAddress, setResolvedAddress] = useState<string>('');
  const [resolving, setResolving] = useState(false);
  const [outsideLagos, setOutsideLagos] = useState(false);
  const [mapReady, setMapReady] = useState(false);

  // Search States
  const autocompleteServiceRef = useRef<any>(null);
  const placesServiceRef = useRef<any>(null);
  const searchDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const sessionTokenRef = useRef<any>(null);
  const latestSearchRequestIdRef = useRef(0);
  const lastSearchQueryRef = useRef('');
  const reverseGeocodeCacheRef = useRef<Map<string, string>>(new Map());
  const lastReverseGeocodeCenterRef = useRef<{ lat: number; lng: number } | null>(null);
  const skipNextIdleReverseGeocodeRef = useRef(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isSearching, setIsSearching] = useState(false);

  const resetAutocompleteSession = () => {
    sessionTokenRef.current = null;
    lastSearchQueryRef.current = '';
  };

  const ensureSessionToken = () => {
    if (!sessionTokenRef.current && window.google?.maps?.places?.AutocompleteSessionToken) {
      sessionTokenRef.current = new window.google.maps.places.AutocompleteSessionToken();
    }
    return sessionTokenRef.current;
  };

  // ── Initialise map once panel is mounted ──────────────────────
  useEffect(() => {
    const init = () => {
      if (!mapContainerRef.current || !window.google?.maps) return;

      const map = new window.google.maps.Map(mapContainerRef.current, {
        center: LAGOS_CENTER,
        zoom: 14,
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: false,
        zoomControl: true,
        clickableIcons: false,
        styles: [
          { featureType: 'poi', elementType: 'labels', stylers: [{ visibility: 'off' }] },
          { featureType: 'transit', stylers: [{ visibility: 'off' }] },
        ],
      });

      mapInstanceRef.current = map;
      geocoderRef.current = new window.google.maps.Geocoder();
      if (window.google.maps.places) {
        autocompleteServiceRef.current = new window.google.maps.places.AutocompleteService();
        const dummyDiv = document.createElement('div');
        placesServiceRef.current = new window.google.maps.places.PlacesService(dummyDiv);
      }
      setMapReady(true);

      // Fire reverse-geocode after map idles (user stopped dragging)
      map.addListener('idle', () => {
        const center = map.getCenter();
        if (!center) return;
        const lat = center.lat();
        const lng = center.lng();

        // Debounce
        if (debounceRef.current) clearTimeout(debounceRef.current);
        debounceRef.current = setTimeout(() => {
          if (skipNextIdleReverseGeocodeRef.current) {
            skipNextIdleReverseGeocodeRef.current = false;
            setResolving(false);
            return;
          }

          const centerPoint = { lat, lng };
          if (!isInLagos(lat, lng)) {
            setOutsideLagos(true);
            setResolvedAddress('');
            setResolving(false);
            return;
          }

          if (!hasMeaningfulCenterChange(lastReverseGeocodeCenterRef.current, centerPoint)) {
            return;
          }

          const cachedAddress = reverseGeocodeCacheRef.current.get(reverseGeocodeCacheKey(lat, lng));
          if (cachedAddress) {
            lastReverseGeocodeCenterRef.current = centerPoint;
            setOutsideLagos(false);
            setResolvedAddress(cachedAddress);
            setResolving(false);
            return;
          }

          setOutsideLagos(false);
          setResolving(true);

          geocoderRef.current.geocode(
            { location: { lat, lng } },
            (results: any[], status: string) => {
              setResolving(false);
              if (status === 'OK' && results[0]) {
                const formattedAddress = results[0].formatted_address;
                lastReverseGeocodeCenterRef.current = centerPoint;
                reverseGeocodeCacheRef.current.set(reverseGeocodeCacheKey(lat, lng), formattedAddress);
                setResolvedAddress(formattedAddress);
              } else {
                // Fallback to lat/lng string
                lastReverseGeocodeCenterRef.current = centerPoint;
                setResolvedAddress(`${lat.toFixed(6)}, ${lng.toFixed(6)}`);
              }
            }
          );
        }, 600);
      });
    };

    if (window.google?.maps) {
      init();
    } else {
      window.addEventListener('google-maps-loaded', init, { once: true });
    }

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current);
    };
  }, []);

  // Block body scroll while modal is open
  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = prev; };
  }, []);

  const handleConfirm = () => {
    if (!resolvedAddress || outsideLagos) return;
    const center = mapInstanceRef.current.getCenter();
    if (center) {
      onConfirm(resolvedAddress, center.lat(), center.lng());
    } else {
      onConfirm(resolvedAddress, 0, 0); // Should not happen
    }
  };

  const handleSearchInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value);

    if (!value.trim() || value.length < 3) {
      setSuggestions([]);
      setShowSuggestions(false);
      setIsSearching(false);
      resetAutocompleteSession();
      return;
    }

    if (!autocompleteServiceRef.current) return;

    if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current);

    const requestId = ++latestSearchRequestIdRef.current;

    searchDebounceRef.current = setTimeout(() => {
      setIsSearching(true);

      const lagosBounds = new window.google.maps.LatLngBounds(
        new window.google.maps.LatLng(LAGOS_BOUNDS.minLat, LAGOS_BOUNDS.minLng),
        new window.google.maps.LatLng(LAGOS_BOUNDS.maxLat, LAGOS_BOUNDS.maxLng)
      );

      const lower = value.toLowerCase();
      const query = lower.includes('lagos') || lower.includes('nigeria')
        ? value
        : value.trimEnd().replace(/,\s*$/, '') + ', Lagos, Nigeria';

      const normalizedQuery = query.trim().toLowerCase();
      if (normalizedQuery === lastSearchQueryRef.current) {
        setIsSearching(false);
        return;
      }
      lastSearchQueryRef.current = normalizedQuery;

      const sessionToken = ensureSessionToken();

      autocompleteServiceRef.current.getPlacePredictions(
        {
          input: query,
          componentRestrictions: { country: 'ng' },
          bounds: lagosBounds,
          ...(sessionToken ? { sessionToken } : {}),
        },
        (predictions: any[] | null, status: string) => {
          if (requestId !== latestSearchRequestIdRef.current) return;
          setIsSearching(false);
          if (status === 'OK' && predictions) {
            setSuggestions(predictions.slice(0, 5));
            setShowSuggestions(true);
          } else {
            setSuggestions([]);
            setShowSuggestions(false);
          }
        }
      );
    }, 400);
  };

  const handleSelectSuggestion = (suggestion: any) => {
    setShowSuggestions(false);
    setSuggestions([]);
    latestSearchRequestIdRef.current += 1;

    if (!placesServiceRef.current || !mapInstanceRef.current) {
      resetAutocompleteSession();
      setSearchQuery(suggestion.description);
      return;
    }

    setResolving(true);
    const sessionToken = sessionTokenRef.current;

    placesServiceRef.current.getDetails(
      {
        placeId: suggestion.place_id,
        fields: ['formatted_address', 'geometry.location'],
        ...(sessionToken ? { sessionToken } : {}),
      },
      (place: any, status: string) => {
        resetAutocompleteSession();

        if (status === window.google.maps.places.PlacesServiceStatus.OK && place?.geometry?.location) {
          const loc = place.geometry.location;
          const lat = loc.lat();
          const lng = loc.lng();

          if (!isInLagos(lat, lng)) {
            setOutsideLagos(true);
            setResolving(false);
            setResolvedAddress('');
            setSearchQuery(place.formatted_address || suggestion.description);
            mapInstanceRef.current.panTo(loc);
            return;
          }

          const formattedAddress = place.formatted_address || suggestion.description;
          setSearchQuery(formattedAddress);
          setOutsideLagos(false);
          setResolvedAddress(formattedAddress);
          lastReverseGeocodeCenterRef.current = { lat, lng };
          reverseGeocodeCacheRef.current.set(reverseGeocodeCacheKey(lat, lng), formattedAddress);
          skipNextIdleReverseGeocodeRef.current = true;
          mapInstanceRef.current.panTo(loc);
          setResolving(false);
          return;
        }

        setSearchQuery(suggestion.description);
        setResolving(false);
      }
    );
  };

  return (
    /* Backdrop */
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 10000,
        background: 'rgba(15,23,42,0.65)', backdropFilter: 'blur(4px)',
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        padding: 16,
        animation: 'mpFadeIn 0.2s ease',
      }}
      onMouseDown={e => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div style={{
        width: '100%', maxWidth: 680, height: 560,
        borderRadius: 20, overflow: 'hidden',
        boxShadow: '0 32px 80px rgba(0,0,0,0.35)',
        display: 'flex', flexDirection: 'column',
        background: '#fff',
        animation: 'mpSlideUp 0.25s cubic-bezier(0.34,1.56,0.64,1)',
      }}>

        {/* ── Modal header ── */}
        <div style={{
          padding: '14px 18px',
          background: 'linear-gradient(135deg, #1B2A4A 0%, #0f1b33 100%)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 36, height: 36, borderRadius: 10,
              background: 'linear-gradient(135deg, #E8A838, #F5C563)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 18, flexShrink: 0,
            }}>
              📍
            </div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#fff' }}>Pick Location on Map</div>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginTop: 1 }}>
                Drag the map or search to position the pin
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'rgba(255,255,255,0.1)', border: 'none',
              borderRadius: 8, width: 30, height: 30,
              cursor: 'pointer', color: 'rgba(255,255,255,0.7)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              transition: 'background 0.15s',
            }}
            onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.2)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.1)')}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* ── Search Bar overlay ── */}
        <div style={{ position: 'relative', padding: '12px 16px', background: '#fff', borderBottom: '1px solid #e2e8f0', zIndex: 30 }}>
          <div style={{ position: 'relative' }}>
            <div style={{ position: 'absolute', left: 12, top: 12, color: '#94a3b8' }}>🔍</div>
            <input
              type="text"
              value={searchQuery}
              onChange={handleSearchInput}
              onFocus={(e) => {
                e.target.style.borderColor = '#1B2A4A';
                if (suggestions.length > 0) setShowSuggestions(true);
              }}
              placeholder="Search for landmark, street, or area..."
              style={{
                width: '100%', padding: '12px 12px 12px 36px', height: 44,
                border: '1.5px solid #e2e8f0', borderRadius: 10,
                fontSize: 14, fontWeight: 500, outline: 'none', color: '#1B2A4A',
                fontFamily: 'inherit',
                transition: 'border-color 0.2s'
              }}
              onBlur={(e) => e.target.style.borderColor = '#e2e8f0'}
            />
            {isSearching && (
              <div style={{ position: 'absolute', right: 12, top: 14, fontSize: 12, color: '#94a3b8' }}>⏳</div>
            )}
          </div>

          {/* Suggestions dropdown */}
          {showSuggestions && suggestions.length > 0 && (
            <div style={{
              position: 'absolute', top: '100%', left: 16, right: 16, marginTop: 4,
              background: '#fff', borderRadius: 10, border: '1px solid #e2e8f0',
              boxShadow: '0 10px 25px rgba(0,0,0,0.1)', overflow: 'hidden', zIndex: 40
            }}>
              {suggestions.map((s, i) => (
                <div key={s.place_id}
                  onClick={() => handleSelectSuggestion(s)}
                  style={{
                    padding: '12px 14px', borderBottom: i < suggestions.length - 1 ? '1px solid #f1f5f9' : 'none',
                    cursor: 'pointer', display: 'flex', alignItems: 'flex-start', gap: 10,
                    transition: 'background 0.15s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = '#f8fafc'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                >
                  <span style={{ color: '#E8A838', marginTop: 2 }}>📍</span>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>{s.structured_formatting?.main_text || s.description}</div>
                    <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>{s.structured_formatting?.secondary_text || ''}</div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Click outside search overlay to close dropdown */}
          {showSuggestions && (
            <div
              style={{ position: 'fixed', inset: 0, zIndex: 35 }}
              onClick={() => setShowSuggestions(false)}
            />
          )}
        </div>

        {/* ── Map container ── */}
        <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
          {/* The actual Google Map */}
          <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />

          {/* Fixed crosshair pin — always centered, map moves under it */}
          <div style={{
            position: 'absolute', top: '50%', left: '50%',
            transform: 'translate(-50%, -100%)',
            pointerEvents: 'none',
            zIndex: 10,
            display: 'flex', flexDirection: 'column', alignItems: 'center',
            filter: outsideLagos ? 'grayscale(1) opacity(0.5)' : 'none',
            transition: 'filter 0.2s',
          }}>
            {/* Pin head */}
            <div style={{
              width: 36, height: 36,
              borderRadius: '50% 50% 50% 0',
              transform: 'rotate(-45deg)',
              background: resolving
                ? '#94a3b8'
                : outsideLagos ? '#ef4444' : 'linear-gradient(135deg, #E8A838, #F5C563)',
              border: '3px solid #fff',
              boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              transition: 'background 0.2s',
            }}>
              <div style={{ transform: 'rotate(45deg)', fontSize: 14 }}>
                {resolving ? '⏳' : outsideLagos ? '⚠️' : '📍'}
              </div>
            </div>
            {/* Pin tail shadow */}
            <div style={{
              width: 8, height: 8, borderRadius: '50%',
              background: 'rgba(0,0,0,0.2)',
              marginTop: 2,
              filter: 'blur(2px)',
            }} />
          </div>

          {/* Outside-Lagos warning overlay */}
          {outsideLagos && (
            <div style={{
              position: 'absolute', top: 12, left: '50%', transform: 'translateX(-50%)',
              background: '#fef2f2', border: '1px solid #fecaca',
              borderRadius: 10, padding: '8px 14px',
              fontSize: 12, fontWeight: 600, color: '#dc2626',
              whiteSpace: 'nowrap', zIndex: 20,
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            }}>
              ⚠️ Outside Lagos — move map closer to Lagos
            </div>
          )}

          {/* "Not loaded" fallback */}
          {!mapReady && (
            <div style={{
              position: 'absolute', inset: 0, background: '#f8fafc',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexDirection: 'column', gap: 12,
            }}>
              <div style={{
                width: 36, height: 36,
                border: '3px solid #E8A838', borderTopColor: 'transparent',
                borderRadius: '50%', animation: 'mpSpin 0.7s linear infinite',
              }} />
              <span style={{ fontSize: 13, color: '#94a3b8' }}>Loading map…</span>
            </div>
          )}
        </div>

        {/* ── Bottom confirmation bar ── */}
        <div style={{
          padding: '14px 18px',
          borderTop: '1px solid #e2e8f0',
          background: '#fff',
          flexShrink: 0,
          display: 'flex', alignItems: 'center', gap: 12,
        }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 3 }}>
              Selected Address
            </div>
            <div style={{
              fontSize: 13, fontWeight: 600, color: '#1B2A4A',
              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              minHeight: 20,
            }}>
              {resolving ? (
                <span style={{ color: '#94a3b8' }}>Resolving address…</span>
              ) : outsideLagos ? (
                <span style={{ color: '#ef4444' }}>Move map to Lagos service area</span>
              ) : resolvedAddress || (
                <span style={{ color: '#94a3b8' }}>Drag the map to position the pin</span>
              )}
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              padding: '10px 18px', borderRadius: 10,
              border: '1.5px solid #e2e8f0', background: '#fff',
              fontSize: 13, fontWeight: 600, color: '#64748b',
              cursor: 'pointer', fontFamily: 'inherit', flexShrink: 0,
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={!resolvedAddress || resolving || outsideLagos}
            style={{
              padding: '10px 22px', borderRadius: 10,
              border: 'none',
              background: (!resolvedAddress || resolving || outsideLagos)
                ? '#e2e8f0'
                : 'linear-gradient(135deg, #E8A838, #F5C563)',
              color: (!resolvedAddress || resolving || outsideLagos)
                ? '#94a3b8' : '#1B2A4A',
              fontSize: 13, fontWeight: 700,
              cursor: (!resolvedAddress || resolving || outsideLagos) ? 'not-allowed' : 'pointer',
              fontFamily: 'inherit', flexShrink: 0,
              boxShadow: (!resolvedAddress || resolving || outsideLagos)
                ? 'none' : '0 4px 12px rgba(232,168,56,0.35)',
              transition: 'all 0.15s',
            }}
          >
            Use this address ✓
          </button>
        </div>
      </div>

      <style>{`
        @keyframes mpFadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes mpSlideUp { from { opacity: 0; transform: translateY(20px) scale(0.97); } to { opacity: 1; transform: translateY(0) scale(1); } }
        @keyframes mpSpin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
