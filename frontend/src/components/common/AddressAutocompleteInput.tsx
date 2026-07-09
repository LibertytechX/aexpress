'use client';

import React, { useState, useEffect, useRef } from 'react';
import API from '@/lib/api';

declare global {
  interface Window {
    google: any;
    googleMapsLoaded?: boolean;
  }
}

// Lagos State bounding box — used for both suggestion filtering and post-geocode validation
const LAGOS_BOUNDS = { minLat: 6.25, maxLat: 6.75, minLng: 2.70, maxLng: 3.95 };
const isInLagos = (lat: number, lng: number) =>
  lat >= LAGOS_BOUNDS.minLat && lat <= LAGOS_BOUNDS.maxLat &&
  lng >= LAGOS_BOUNDS.minLng && lng <= LAGOS_BOUNDS.maxLng;

interface AddressAutocompleteInputProps {
  value: string;
  onChange: (value: string) => void;
  onSelect?: (address: string, lat: number, lng: number) => void;
  placeholder?: string;
  style?: React.CSSProperties;
  disabled?: boolean;
  /** If provided, a "Pick on Map" button is shown when no autocomplete results are found. */
  onOpenMapPicker?: () => void;
}

export default function AddressAutocompleteInput({ value, onChange, onSelect, placeholder, style, disabled, onOpenMapPicker }: AddressAutocompleteInputProps) {
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [useAwsFallback, setUseAwsFallback] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);
  const autocompleteService = useRef<any>(null);
  const placesService = useRef<any>(null);
  const sessionTokenRef = useRef<any>(null);
  const latestPredictionRequestIdRef = useRef(0);
  const lastPredictionQueryRef = useRef('');

  const resetAutocompleteSession = () => {
    sessionTokenRef.current = null;
    lastPredictionQueryRef.current = '';
  };

  const ensureSessionToken = () => {
    if (!sessionTokenRef.current && window.google?.maps?.places?.AutocompleteSessionToken) {
      sessionTokenRef.current = new window.google.maps.places.AutocompleteSessionToken();
    }
    return sessionTokenRef.current;
  };

  // Initialize Google Maps services
  useEffect(() => {
    let timeoutId: NodeJS.Timeout;

    const initServices = () => {
      if (window.google && window.google.maps && window.google.maps.places) {
        autocompleteService.current = new window.google.maps.places.AutocompleteService();
        const dummyDiv = document.createElement('div');
        placesService.current = new window.google.maps.places.PlacesService(dummyDiv);
        setError(null);
        setUseAwsFallback(false);
        if (timeoutId) clearTimeout(timeoutId);
      } else {
        console.warn('[AC] Google Maps not loaded, enabling AWS fallback');
        setUseAwsFallback(true);
      }
    };

    if (window.googleMapsLoaded) {
      initServices();
    } else {
      console.log('[AC] Waiting for google-maps-loaded event...');
      window.addEventListener('google-maps-loaded', initServices);
      
      // Proactive timeout: if Google Maps hasn't loaded in 4 seconds, switch to AWS places
      timeoutId = setTimeout(() => {
        if (!window.googleMapsLoaded) {
          console.warn('[AC] Google Maps load timed out, enabling AWS fallback');
          setUseAwsFallback(true);
        }
      }, 4000);

      return () => {
        window.removeEventListener('google-maps-loaded', initServices);
        clearTimeout(timeoutId);
      };
    }
  }, []);

  useEffect(() => {
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node) &&
        inputRef.current && !inputRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch suggestions with debouncing
  const fetchSuggestions = (input: string) => {
    if (!input || input.length < 3) {
      setSuggestions([]);
      setShowDropdown(false);
      setLoading(false);
      resetAutocompleteSession();
      return;
    }

    console.log('[AC] fetchSuggestions for:', input);

    setLoading(true);
    setError(null);

    // Debounce API calls
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    const requestId = ++latestPredictionRequestIdRef.current;

    debounceTimer.current = setTimeout(() => {
      // Append "Lagos, Nigeria" to the raw input when not already present.
      const lower = input.toLowerCase();
      const searchInput =
        lower.includes('lagos') || lower.includes('nigeria')
          ? input
          : input.trimEnd().replace(/,\s*$/, '') + ', Lagos, Nigeria';

      const normalizedQuery = searchInput.trim().toLowerCase();
      if (normalizedQuery === lastPredictionQueryRef.current) {
        setLoading(false);
        return;
      }
      lastPredictionQueryRef.current = normalizedQuery;

      const handleAwsAutocomplete = () => {
        API.Places.autocomplete(searchInput)
          .then((res: any) => {
            if (requestId !== latestPredictionRequestIdRef.current) return;
            setLoading(false);
            if (res.status === 'success' && res.data?.length > 0) {
              setSuggestions(res.data);
              setShowDropdown(true);
              setError(null);
            } else {
              setSuggestions([]);
              setShowDropdown(false);
              setError('Address not found in Lagos — we only deliver within Lagos State.');
            }
          })
          .catch((err: any) => {
            if (requestId !== latestPredictionRequestIdRef.current) return;
            setLoading(false);
            console.error('[AC] AWS autocomplete error:', err);
            setSuggestions([]);
            setShowDropdown(false);
            setError('Failed to fetch address suggestions.');
          });
      };

      if (useAwsFallback || !autocompleteService.current) {
        handleAwsAutocomplete();
        return;
      }

      // Bias results towards Lagos using both bounds + location
      const lagosBounds = new window.google.maps.LatLngBounds(
        new window.google.maps.LatLng(6.25, 2.70),
        new window.google.maps.LatLng(6.75, 3.95)
      );

      const sessionToken = ensureSessionToken();

      const request = {
        input: searchInput,
        bounds: lagosBounds,
        componentRestrictions: { country: 'ng' },
        ...(sessionToken ? { sessionToken } : {}),
      };

      autocompleteService.current.getPlacePredictions(request, (predictions: any[], status: string) => {
        if (requestId !== latestPredictionRequestIdRef.current) return;
        
        if (status === window.google.maps.places.PlacesServiceStatus.OK && predictions?.length > 0) {
          setLoading(false);
          setSuggestions(predictions.slice(0, 8));
          setShowDropdown(true);
          setError(null);
        } else if (status === window.google.maps.places.PlacesServiceStatus.ZERO_RESULTS) {
          setLoading(false);
          setSuggestions([]);
          setShowDropdown(false);
          setError('Address not found in Lagos — we only deliver within Lagos State.');
        } else {
          console.warn('[AC] Google places prediction failed with status:', status, 'falling back to AWS');
          setUseAwsFallback(true);
          handleAwsAutocomplete();
        }
      });
    }, 550); // 550ms debounce
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    onChange(newValue);
    fetchSuggestions(newValue);
  };

  const handleSelectSuggestion = (suggestion: any) => {
    setSuggestions([]);
    setShowDropdown(false);
    setError(null);

    latestPredictionRequestIdRef.current += 1;
    setLoading(true);

    if (suggestion.is_aws || useAwsFallback || !placesService.current) {
      API.Places.details(suggestion.place_id)
        .then((res: any) => {
          setLoading(false);
          resetAutocompleteSession();

          if (res.status === 'success' && res.data) {
            const { formatted_address, lat, lng } = res.data;
            if (!isInLagos(lat, lng)) {
              onChange('');
              setError('⚠️ Outside service area — we only deliver within Lagos State.');
            } else {
              onChange(formatted_address);
              if (onSelect) {
                onSelect(formatted_address, lat, lng);
              }
            }
          } else {
            onChange(suggestion.description);
          }
        })
        .catch((err: any) => {
          setLoading(false);
          resetAutocompleteSession();
          console.error('[AC] AWS details lookup error:', err);
          onChange(suggestion.description);
        });
      return;
    }

    const sessionToken = sessionTokenRef.current;

    placesService.current.getDetails(
      {
        placeId: suggestion.place_id,
        fields: ['formatted_address', 'geometry.location'],
        ...(sessionToken ? { sessionToken } : {}),
      },
      (place: any, status: string) => {
        setLoading(false);
        resetAutocompleteSession();

        if (status === window.google.maps.places.PlacesServiceStatus.OK && place?.geometry?.location) {
          const loc = place.geometry.location;
          if (!isInLagos(loc.lat(), loc.lng())) {
            onChange('');
            setError('⚠️ Outside service area — we only deliver within Lagos State.');
          } else {
            const addr = place.formatted_address || suggestion.description;
            onChange(addr);
            if (onSelect) {
              onSelect(addr, loc.lat(), loc.lng());
            }
          }
          return;
        }

        onChange(suggestion.description); // Details lookup failed, allow through and let backend validate
      }
    );
  };

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      <input
        ref={inputRef}
        value={value}
        onChange={handleInputChange}
        placeholder={placeholder}
        disabled={disabled}
        style={style}
      />

      {/* Loading indicator */}
      {loading && (
        <div style={{
          position: 'absolute',
          right: 12,
          top: '50%',
          transform: 'translateY(-50%)',
          fontSize: 12,
          color: '#94a3b8'
        }}>
          ⏳
        </div>
      )}

      {/* Dropdown with suggestions */}
      {showDropdown && suggestions.length > 0 && (
        <div
          ref={dropdownRef}
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            marginTop: 4,
            background: '#fff',
            border: '1px solid #e2e8f0',
            borderRadius: 10,
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            maxHeight: 240,
            overflowY: 'auto',
            zIndex: 1000
          }}
        >
          {suggestions.map((suggestion, idx) => (
            <div
              key={suggestion.place_id}
              onClick={() => handleSelectSuggestion(suggestion)}
              style={{
                padding: '10px 14px',
                cursor: 'pointer',
                borderBottom: idx < suggestions.length - 1 ? '1px solid #f1f5f9' : 'none',
                fontSize: 13,
                color: '#1e293b',
                transition: 'background 0.15s ease'
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = '#f8fafc'}
              onMouseLeave={(e) => e.currentTarget.style.background = '#fff'}
            >
              <div style={{ display: 'flex', alignItems: 'start', gap: 8 }}>
                <span style={{ color: '#f59e0b', marginTop: 2 }}>📍</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, marginBottom: 2 }}>
                    {suggestion.structured_formatting?.main_text || suggestion.description}
                  </div>
                  {suggestion.structured_formatting?.secondary_text && (
                    <div style={{ fontSize: 11, color: '#64748b' }}>
                      {suggestion.structured_formatting.secondary_text}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error message + optional map picker CTA */}
      {error && value.length >= 3 && !loading && (
        <div style={{ marginTop: 5, paddingLeft: 2 }}>
          <div style={{ fontSize: 11, color: '#ef4444', marginBottom: onOpenMapPicker ? 6 : 0 }}>
            {error} — you can still type it manually.
          </div>
          {onOpenMapPicker && (
            <button
              type="button"
              onClick={onOpenMapPicker}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 5,
                padding: '5px 12px', borderRadius: 8,
                border: '1.5px solid #E8A838',
                background: '#fef3c7',
                color: '#92400e', fontSize: 12, fontWeight: 700,
                cursor: 'pointer', fontFamily: 'inherit',
                transition: 'all 0.15s',
              }}
              onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = '#fde68a'; }}
              onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = '#fef3c7'; }}
            >
              📍 Pick on Map
            </button>
          )}
        </div>
      )}
    </div>
  );
}

