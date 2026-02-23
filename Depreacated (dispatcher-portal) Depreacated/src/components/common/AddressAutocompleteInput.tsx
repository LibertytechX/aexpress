
import { useState, useEffect, useRef } from "react";
import { S } from "../common/theme";

interface AddressAutocompleteInputProps {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    style?: React.CSSProperties;
    disabled?: boolean;
}

declare global {
    interface Window {
        google: any;
        googleMapsLoaded: boolean;
    }
}

export function AddressAutocompleteInput({ value, onChange, placeholder, style, disabled }: AddressAutocompleteInputProps) {
    const [suggestions, setSuggestions] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [showDropdown, setShowDropdown] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const debounceTimer = useRef<any>(null);
    const autocompleteService = useRef<any>(null);
    const placesService = useRef<any>(null);

    // Initialize Google Maps services
    useEffect(() => {
        const initServices = () => {
            if (window.google && window.google.maps && window.google.maps.places) {
                autocompleteService.current = new window.google.maps.places.AutocompleteService();
                // Create a dummy div for PlacesService (required by Google Maps API)
                const dummyDiv = document.createElement('div');
                placesService.current = new window.google.maps.places.PlacesService(dummyDiv);
                setError(null);
            } else {
                setError('Google Maps not loaded');
            }
        };

        if (window.googleMapsLoaded) {
            initServices();
        } else {
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
            // Try to re-init if not ready? Or just fail silently/log.
            // setError('Google Maps not ready');
            return;
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

            autocompleteService.current.getPlacePredictions(request, (predictions: any[], status: any) => {
                setLoading(false);

                if (status === window.google.maps.places.PlacesServiceStatus.OK && predictions) {
                    // Filter to only Lagos addresses? Or keep all Nigeria?
                    // Let's bias to Lagos but allow others.
                    // const lagosResults = predictions.filter(p =>
                    //   p.description.toLowerCase().includes('lagos')
                    // );

                    setSuggestions(predictions);
                    setShowDropdown(true);
                    setError(null);
                } else if (status === window.google.maps.places.PlacesServiceStatus.ZERO_RESULTS) {
                    // setError('No addresses found');
                    setSuggestions([]);
                } else {
                    // setError('Failed to fetch suggestions');
                    setSuggestions([]);
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
                        border: `1px solid ${S.border}`,
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
                                borderBottom: idx < suggestions.length - 1 ? `1px solid ${S.grayBg}` : 'none',
                                fontSize: 13,
                                color: S.navy,
                                transition: 'background 0.15s ease'
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.background = S.grayBg}
                            onMouseLeave={(e) => e.currentTarget.style.background = '#fff'}
                        >
                            <div style={{ display: 'flex', alignItems: 'start', gap: 8 }}>
                                <span style={{ color: S.gold, marginTop: 2 }}>📍</span>
                                <div style={{ flex: 1 }}>
                                    <div style={{ fontWeight: 600, marginBottom: 2 }}>
                                        {suggestion.structured_formatting?.main_text || suggestion.description}
                                    </div>
                                    {suggestion.structured_formatting?.secondary_text && (
                                        <div style={{ fontSize: 11, color: S.textMuted }}>
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
                    color: S.red,
                    marginTop: 4,
                    paddingLeft: 4
                }}>
                    {error}
                </div>
            )}
        </div>
    );
}
