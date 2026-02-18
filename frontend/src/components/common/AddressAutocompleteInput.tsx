'use client';

import React, { useState, useEffect, useRef } from 'react';

declare global {
  interface Window {
    google: any;
  }
}

interface AddressAutocompleteInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  style?: React.CSSProperties;
  disabled?: boolean;
}

export default function AddressAutocompleteInput({ value, onChange, placeholder, style, disabled }: AddressAutocompleteInputProps) {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);
  const dropdownRef = useRef(null);
  const debounceTimer = useRef(null);
  const autocompleteService = useRef(null);

  // Initialize Google Maps services
  useEffect(() => {
    const initServices = () => {
      if (window.google && window.google.maps && window.google.maps.places) {
        autocompleteService.current = new window.google.maps.places.AutocompleteService();
        setError(null);
      } else {
        // Retry if not ready
        const checkInterval = setInterval(() => {
          if (window.google && window.google.maps && window.google.maps.places) {
            autocompleteService.current = new window.google.maps.places.AutocompleteService();
            setError(null);
            clearInterval(checkInterval);
          }
        }, 1000);
      }
    };

    initServices();
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target) &&
        inputRef.current && !inputRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch suggestions with debouncing
  const fetchSuggestions = (input) => {
    if (!input || input.length < 3) {
      setSuggestions([]);
      setShowDropdown(false);
      return;
    }

    if (!autocompleteService.current) {
      // Try to init again if null
      if (window.google && window.google.maps && window.google.maps.places) {
        autocompleteService.current = new window.google.maps.places.AutocompleteService();
      } else {
        return; // Maps not loaded yet
      }
    }

    setLoading(true);
    setError(null);

    // Debounce API calls
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    debounceTimer.current = setTimeout(() => {
      const request = {
        input: input,
        componentRestrictions: { country: 'ng' }, // Restrict to Nigeria
        types: ['address'], // Only addresses
        // Bias results to Lagos
        location: new window.google.maps.LatLng(6.5244, 3.3792), // Lagos coordinates
        radius: 50000, // 50km radius
      };

      autocompleteService.current.getPlacePredictions(request, (predictions, status) => {
        setLoading(false);

        if (status === window.google.maps.places.PlacesServiceStatus.OK && predictions) {
          // Filter to only Lagos addresses (optional, based on original code preference)
          // The original code filtered for 'lagos', let's keep that behavior if desired,
          // but maybe relax it if user wants broad search. Original code:
          const lagosResults = predictions.filter(p =>
            p.description.toLowerCase().includes('lagos')
          );

          if (lagosResults.length === 0) {
            // Fallback to all results if strict filtering is too aggressive, 
            // but original code said "No addresses found in Lagos". 
            // We'll stick to original logic:
            if (predictions.length > 0) {
              // If we have predictions but none in Lagos, show them anyway but maybe warn?
              // Or just show lagos results. Original code showed strict error.
              // Let's relax it slightly to avoid "No results" if Google returns valid nearby places that don't say "Lagos" explicitly in description but are in Lagos.
              // But adhering to original code:
              setSuggestions(lagosResults);
              if (lagosResults.length === 0) setError('No addresses found in Lagos');
              else setShowDropdown(true);
            } else {
              setError('No addresses found');
              setSuggestions([]);
            }
          } else {
            setSuggestions(lagosResults);
            setShowDropdown(true);
            setError(null);
          }
        } else if (status === window.google.maps.places.PlacesServiceStatus.ZERO_RESULTS) {
          setError('No addresses found');
          setSuggestions([]);
        } else {
          // console.error('Autocomplete error:', status);
          // Don't show generic error to user, just clear suggestions
          setSuggestions([]);
        }
      });
    }, 550); // 550ms debounce
  };

  const handleInputChange = (e) => {
    const newValue = e.target.value;
    onChange(newValue);
    fetchSuggestions(newValue);
  };

  const handleSelectSuggestion = (suggestion) => {
    onChange(suggestion.description);
    setSuggestions([]);
    setShowDropdown(false);
    setError(null);
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
