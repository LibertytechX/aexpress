'use client';

import React, { useState, useEffect, useRef } from 'react';

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
  placeholder?: string;
  style?: React.CSSProperties;
  disabled?: boolean;
}

export default function AddressAutocompleteInput({ value, onChange, placeholder, style, disabled }: AddressAutocompleteInputProps) {
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);
  const autocompleteService = useRef<any>(null);
  const placesService = useRef<any>(null);
  const geocoderRef = useRef<any>(null);

  // Initialize Google Maps services
  useEffect(() => {
    const initServices = () => {
      if (window.google && window.google.maps && window.google.maps.places) {
        autocompleteService.current = new window.google.maps.places.AutocompleteService();
        const dummyDiv = document.createElement('div');
        placesService.current = new window.google.maps.places.PlacesService(dummyDiv);
        geocoderRef.current = new window.google.maps.Geocoder();
        setError(null);
      } else {
        setError('Google Maps not loaded');
      }
    };

    if (window.googleMapsLoaded) {
      initServices();
    } else {
      console.log('[AC] Waiting for google-maps-loaded event...');
      window.addEventListener('google-maps-loaded', initServices);
      return () => window.removeEventListener('google-maps-loaded', initServices);
    }
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
      return;
    }

    if (!autocompleteService.current) {
      console.error('[AC] fetchSuggestions called but autocompleteService is null');
      setError('Google Maps not ready');
      return;
    }
    console.log('[AC] fetchSuggestions for:', input);

    setLoading(true);
    setError(null);

    // Debounce API calls
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    debounceTimer.current = setTimeout(() => {
      // Bias results towards Lagos (bounds is a preference, not a hard filter for AutocompleteService)
      const lagosBounds = new window.google.maps.LatLngBounds(
        new window.google.maps.LatLng(6.25, 2.70),
        new window.google.maps.LatLng(6.75, 3.95)
      );
      const request = {
        input,
        bounds: lagosBounds,
        componentRestrictions: { country: 'ng' },
      };

      autocompleteService.current.getPlacePredictions(request, (predictions: any[], status: string) => {
        setLoading(false);
        if (status === window.google.maps.places.PlacesServiceStatus.OK && predictions?.length > 0) {
          // Keep only predictions that reference Lagos — no fallback to non-Lagos results
          const lagosOnly = predictions.filter(p =>
            p.terms?.some((t: any) => /lagos/i.test(t.value)) ||
            /lagos/i.test(p.description)
          );
          if (lagosOnly.length > 0) {
            setSuggestions(lagosOnly.slice(0, 8));
            setShowDropdown(true);
            setError(null);
          } else {
            setSuggestions([]);
            setShowDropdown(false);
            setError('Address not found in Lagos — we only deliver within Lagos State.');
          }
        } else {
          setSuggestions([]);
          setShowDropdown(false);
          setError('Address not found in Lagos — we only deliver within Lagos State.');
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
    // Geocode the selection and validate it falls within Lagos State
    if (geocoderRef.current) {
      geocoderRef.current.geocode({ placeId: suggestion.place_id }, (results: any[], status: string) => {
        if (status === 'OK' && results[0]?.geometry) {
          const loc = results[0].geometry.location;
          if (!isInLagos(loc.lat(), loc.lng())) {
            onChange('');
            setError('⚠️ Outside service area — we only deliver within Lagos State.');
          } else {
            onChange(suggestion.description);
          }
        } else {
          onChange(suggestion.description); // geocode failed, allow through and let backend validate
        }
      });
    } else {
      onChange(suggestion.description);
    }
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

      {/* Error message */}
      {error && value.length >= 3 && !loading && (
        <div style={{
          fontSize: 11,
          color: '#ef4444',
          marginTop: 4,
          paddingLeft: 4
        }}>
          {error} - You can still enter address manually
        </div>
      )}
    </div>
  );
}

