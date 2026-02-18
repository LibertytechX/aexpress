'use client';

import React, { useEffect, useRef, useState } from 'react';
import { S } from '@/lib/theme';
import Icons from '@/components/Icons';

declare global {
  interface Window {
    google: any;
  }
}

export default function DeliveryMapView({ pickupAddress, dropoffs, vehicle, totalDeliveries, totalCost, onRouteCalculated }) {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef([]);
  const directionsRendererRef = useRef(null);
  const animationIntervalRef = useRef(null);

  // State for route information
  const [routeDistance, setRouteDistance] = useState(null); // in kilometers
  const [routeDuration, setRouteDuration] = useState(null); // in minutes
  const [routeDurationInTraffic, setRouteDurationInTraffic] = useState(null); // in minutes

  // Helper function to format duration
  const formatDuration = (minutes) => {
    if (!minutes) return '';
    if (minutes < 60) {
      return `${minutes} min`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours} hr ${mins} min` : `${hours} hr`;
  };

  // Function to animate the pulse along the route
  const startPulseAnimation = () => {
    // Clear any existing animation
    if (animationIntervalRef.current) {
      clearInterval(animationIntervalRef.current);
    }

    let offset = 0;
    const speed = 2; // Pixels per frame (adjust for speed)

    // Safety check for DirectionsRenderer access
    if (!directionsRendererRef.current) return;

    animationIntervalRef.current = setInterval(() => {
      offset = (offset + speed) % 200; // Reset after 200px (2 complete cycles)

      if (directionsRendererRef.current) {
        // Need to check if map is still mounted
        try {
          const polylineOptions = directionsRendererRef.current.get('polylineOptions');
          if (polylineOptions && polylineOptions.icons) {
            // Update the offset of the pulse icon
            polylineOptions.icons[0].offset = offset + 'px';
            directionsRendererRef.current.setOptions({ polylineOptions });
          }
        } catch (e) {
          clearInterval(animationIntervalRef.current);
        }
      }
    }, 50); // Update every 50ms for smooth animation (~20 fps)
  };

  useEffect(() => {
    // Wait for Google Maps to load
    if (!window.google || !window.google.maps) {
      console.error('Google Maps not loaded');
      return;
    }

    // Initialize map
    const initMap = () => {
      if (!mapRef.current) return;

      // Create map centered on Lagos
      const map = new window.google.maps.Map(mapRef.current, {
        center: { lat: 6.5244, lng: 3.3792 }, // Lagos, Nigeria
        zoom: 12,
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: true,
        zoomControl: true,
        styles: [
          {
            featureType: "poi",
            elementType: "labels",
            stylers: [{ visibility: "off" }]
          }
        ]
      });

      mapInstanceRef.current = map;

      // Initialize directions renderer with burnt orange color and animated pulse
      directionsRendererRef.current = new window.google.maps.DirectionsRenderer({
        map: map,
        suppressMarkers: true, // We'll add custom markers
        polylineOptions: {
          strokeColor: '#E8A838', // Burnt orange to match app theme (S.gold)
          strokeWeight: 4,
          strokeOpacity: 0.7,
          icons: [{
            icon: {
              path: window.google.maps.SymbolPath.CIRCLE,
              scale: 4,
              fillColor: '#ffffff',
              fillOpacity: 0.8,
              strokeColor: '#ffffff',
              strokeWeight: 2,
              strokeOpacity: 0.6
            },
            offset: '0%',
            repeat: '100px'
          }]
        }
      });
    };

    initMap();

    // Cleanup
    return () => {
      if (markersRef.current) {
        markersRef.current.forEach(marker => marker.setMap(null));
        markersRef.current = [];
      }
      if (directionsRendererRef.current) {
        directionsRendererRef.current.setMap(null);
      }
      if (animationIntervalRef.current) {
        clearInterval(animationIntervalRef.current);
      }
    };
  }, []);

  // Update markers and route when addresses change
  useEffect(() => {
    if (!mapInstanceRef.current || !window.google) return;

    const updateMapMarkersAndRoute = async () => {
      const map = mapInstanceRef.current;
      const geocoder = new window.google.maps.Geocoder();

      // Clear existing markers
      markersRef.current.forEach(marker => marker.setMap(null));
      markersRef.current = [];

      // Geocode pickup address
      const geocodeAddress = (address) => {
        return new Promise((resolve) => {
          geocoder.geocode({ address: address + ', Lagos, Nigeria' }, (results, status) => {
            if (status === 'OK' && results[0]) {
              resolve(results[0].geometry.location);
            } else {
              console.warn(`Geocoding failed for ${address}:`, status);
              resolve(null);
            }
          });
        });
      };

      try {
        // Geocode pickup
        const pickupLocation = await geocodeAddress(pickupAddress);

        if (pickupLocation) {
          // Add green pickup marker
          const pickupMarker = new window.google.maps.Marker({
            position: pickupLocation,
            map: map,
            title: 'Pickup: ' + pickupAddress,
            icon: {
              path: window.google.maps.SymbolPath.CIRCLE,
              scale: 10,
              fillColor: '#10b981',
              fillOpacity: 1,
              strokeColor: '#ffffff',
              strokeWeight: 3
            },
            label: {
              text: '📍',
              fontSize: '16px'
            }
          });
          markersRef.current.push(pickupMarker);
        }

        // Geocode dropoffs
        const dropoffLocations = [];
        // Ensure dropoffs is an array and filter valid ones
        const validDropoffs = Array.isArray(dropoffs) ? dropoffs.filter(d => d.address) : [];

        for (let i = 0; i < validDropoffs.length; i++) {
          const dropoff = validDropoffs[i];
          const location = await geocodeAddress(dropoff.address);

          if (location) {
            dropoffLocations.push({ location, dropoff, index: i });

            // Add numbered gold marker for each dropoff
            const dropoffMarker = new window.google.maps.Marker({
              position: location,
              map: map,
              title: `Delivery ${i + 1}: ${dropoff.address}`,
              icon: {
                path: window.google.maps.SymbolPath.CIRCLE,
                scale: 12,
                fillColor: '#E8A838',
                fillOpacity: 1,
                strokeColor: '#ffffff',
                strokeWeight: 3
              },
              label: {
                text: String(i + 1),
                color: '#1B2A4A',
                fontSize: '12px',
                fontWeight: 'bold'
              }
            });
            markersRef.current.push(dropoffMarker);
          }
        }

        // Draw route if we have pickup and at least one dropoff
        if (pickupLocation && dropoffLocations.length > 0 && directionsRendererRef.current) {
          const directionsService = new window.google.maps.DirectionsService();

          // Prepare waypoints for multi-stop route
          const waypoints = dropoffLocations.slice(0, -1).map(d => ({
            location: d.location,
            stopover: true
          }));

          const request = {
            origin: pickupLocation,
            destination: dropoffLocations[dropoffLocations.length - 1].location,
            waypoints: waypoints,
            travelMode: window.google.maps.TravelMode.DRIVING,
            optimizeWaypoints: true
          };

          directionsService.route(request, (result, status) => {
            if (status === 'OK') {
              directionsRendererRef.current.setDirections(result);

              // Extract distance and duration from route
              if (result.routes && result.routes[0] && result.routes[0].legs) {
                let totalDistanceMeters = 0;
                let totalDurationSeconds = 0;
                let totalDurationInTrafficSeconds = 0;
                let hasTrafficData = false;

                // Sum up all legs (for multi-stop routes)
                result.routes[0].legs.forEach(leg => {
                  if (leg.distance && leg.distance.value) {
                    totalDistanceMeters += leg.distance.value;
                  }
                  if (leg.duration && leg.duration.value) {
                    totalDurationSeconds += leg.duration.value;
                  }
                  if (leg.duration_in_traffic && leg.duration_in_traffic.value) {
                    totalDurationInTrafficSeconds += leg.duration_in_traffic.value;
                    hasTrafficData = true;
                  }
                });

                // Convert to user-friendly units
                const distanceKm = (totalDistanceMeters / 1000).toFixed(1); // kilometers with 1 decimal
                const durationMin = Math.round(totalDurationSeconds / 60); // minutes
                const durationInTrafficMin = hasTrafficData ? Math.round(totalDurationInTrafficSeconds / 60) : null;

                // Update state
                setRouteDistance(parseFloat(distanceKm));
                setRouteDuration(durationMin);
                setRouteDurationInTraffic(durationInTrafficMin);

                // Notify parent component of route calculation
                if (onRouteCalculated) {
                  onRouteCalculated(parseFloat(distanceKm), durationMin);
                }
              }

              // Re-apply polyline options with icons after setDirections
              // (setDirections replaces the polyline, losing our custom icons)
              const polylineOptions = {
                strokeColor: '#E8A838',
                strokeWeight: 4,
                strokeOpacity: 0.7,
                icons: [{
                  icon: {
                    path: window.google.maps.SymbolPath.CIRCLE,
                    scale: 4,
                    fillColor: '#ffffff',
                    fillOpacity: 0.8,
                    strokeColor: '#ffffff',
                    strokeWeight: 2,
                    strokeOpacity: 0.6
                  },
                  offset: '0%',
                  repeat: '100px'
                }]
              };
              directionsRendererRef.current.setOptions({ polylineOptions });

              // Start animated pulse effect
              startPulseAnimation();
            } else {
              console.warn('Directions request failed:', status);
            }
          });
        }

        // Fit bounds to show all markers
        if (markersRef.current.length > 0) {
          const bounds = new window.google.maps.LatLngBounds();
          markersRef.current.forEach(marker => {
            bounds.extend(marker.getPosition());
          });
          map.fitBounds(bounds);

          // Add padding
          const padding = { top: 50, right: 50, bottom: 100, left: 50 };

          // Small delay to ensure map is ready for bounds change
          setTimeout(() => {
            map.fitBounds(bounds, padding);
          }, 100);
        }

      } catch (error) {
        console.error('Error updating map:', error);
      }
    };

    if (pickupAddress && dropoffs.length > 0) {
      updateMapMarkersAndRoute();
    }
  }, [pickupAddress, dropoffs]);

  return (
    <div style={{ flex: 1, minWidth: 0, minHeight: 520, borderRadius: 14, overflow: "hidden", position: "relative", border: "1px solid #e2e8f0" }}>
      {/* Google Map Container */}
      <div ref={mapRef} style={{ width: "100%", height: "100%", position: "absolute", inset: 0 }} />

      {/* Summary card on map */}
      {totalDeliveries > 0 && totalCost > 0 && (
        <div style={{
          position: "absolute", bottom: 14, left: 14, right: 14, zIndex: 10,
          background: "rgba(255,255,255,0.95)", backdropFilter: "blur(8px)",
          borderRadius: 12, padding: "12px 16px", boxShadow: "0 2px 12px rgba(0,0,0,0.1)",
          display: "flex", alignItems: "center", justifyContent: "space-between"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 36, height: 36, borderRadius: 8, background: S.goldPale, display: "flex", alignItems: "center", justifyContent: "center", color: S.gold }}>
              {/* Simplified vehicle icon for now, or assume Vehicle Icon passed/imported */}
              {vehicle === "Bike" ? Icons.bike : vehicle === "Car" ? Icons.car : Icons.van}
            </div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: S.navy }}>{totalDeliveries} × {vehicle} Delivery</div>
              <div style={{ fontSize: 11, color: S.grayLight }}>from {pickupAddress.split(",")[0]}</div>
              {/* Distance and Duration Row */}
              {(routeDistance || routeDuration) && (
                <div style={{ fontSize: 11, color: S.gray, marginTop: 4, display: "flex", alignItems: "center", gap: 8 }}>
                  {routeDistance && (
                    <span style={{ display: "flex", alignItems: "center", gap: 3 }}>
                      <span>📏</span>
                      <span>{routeDistance} km</span>
                    </span>
                  )}
                  {routeDistance && routeDuration && <span>•</span>}
                  {routeDuration && (
                    <span style={{ display: "flex", alignItems: "center", gap: 3 }}>
                      <span>🕐</span>
                      <span>
                        {formatDuration(routeDuration)}
                        {routeDurationInTraffic && routeDurationInTraffic !== routeDuration && (
                          <span style={{ color: S.grayLight }}> ({formatDuration(routeDurationInTraffic)} in traffic)</span>
                        )}
                      </span>
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
          <div style={{ fontSize: 18, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono', monospace" }}>₦{totalCost.toLocaleString()}</div>
        </div>
      )}

      {/* Location badge */}
      <div style={{ position: "absolute", top: 10, right: 10, background: "rgba(255,255,255,0.85)", borderRadius: 6, padding: "4px 8px", fontSize: 10, color: S.grayLight, zIndex: 10 }}>
        🗺️ Lagos, Nigeria
      </div>
    </div>
  );
}
