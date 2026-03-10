import { useRef, useState, useEffect } from "react";
import { S } from "../common/theme";

// ─── DELIVERY ROUTE MAP (Google Maps) ───────────────────────────
export function DeliveryRouteMap({ order, rider }: any) {
    const mapRef = useRef<HTMLDivElement>(null);
    const mapInstanceRef = useRef<any>(null);
    const markersRef = useRef<any[]>([]);
    const directionsRendererRef = useRef<any>(null);
    const [mapStatus, setMapStatus] = useState('loading');
    const [mapReady, setMapReady] = useState(false);

    // Effect 1: Initialize the Google Map (once)
    useEffect(() => {
        const initializeMap = () => {
            if (!mapRef.current || mapInstanceRef.current) return;
            const map = new (window as any).google.maps.Map(mapRef.current, {
                center: { lat: 6.5244, lng: 3.3792 },
                zoom: 12,
                mapTypeControl: false,
                streetViewControl: false,
                fullscreenControl: true,
                zoomControl: true,
                styles: [{ featureType: "poi", elementType: "labels", stylers: [{ visibility: "off" }] }]
            });
            mapInstanceRef.current = map;
            directionsRendererRef.current = new (window as any).google.maps.DirectionsRenderer({
                map: map,
                suppressMarkers: true,
                polylineOptions: {
                    strokeColor: '#E8A838',
                    strokeWeight: 4,
                    strokeOpacity: 0.7,
                    icons: [{ icon: { path: (window as any).google.maps.SymbolPath.CIRCLE, scale: 4 }, offset: '0', repeat: '100px' }]
                }
            });
            setMapReady(true);
        };

        let unsubscribe: any = null;
        if ((window as any).google && (window as any).google.maps) {
            initializeMap();
        } else {
            window.addEventListener('google-maps-loaded', initializeMap);
            unsubscribe = () => window.removeEventListener('google-maps-loaded', initializeMap);
        }

        return () => {
            if (unsubscribe) unsubscribe();
            markersRef.current.forEach(m => m.setMap(null));
            markersRef.current = [];
            if (directionsRendererRef.current) { directionsRendererRef.current.setMap(null); directionsRendererRef.current = null; }
            mapInstanceRef.current = null;
        };
    }, []);

    // Effect 2: Update markers + route whenever order/rider changes
    useEffect(() => {
        if (!mapReady || !mapInstanceRef.current || !(window as any).google) return;
        const map = mapInstanceRef.current;
        const geocoder = new (window as any).google.maps.Geocoder();

        const geocodeAddr = (address: string) => new Promise((resolve) => {
            geocoder.geocode({ address: address + ', Lagos, Nigeria' }, (results: any, status: any) => {
                resolve((status === 'OK' && results[0]) ? results[0].geometry.location : null);
            });
        });

        (async () => {
            // Clear previous markers and route
            markersRef.current.forEach(m => m.setMap(null));
            markersRef.current = [];
            if (directionsRendererRef.current) directionsRendererRef.current.setDirections({ routes: [] });

            const [pickupLoc, dropoffLoc] = await Promise.all([
                geocodeAddr(order.pickup),
                geocodeAddr(order.dropoff),
            ]);
            if (!pickupLoc || !dropoffLoc) { setMapStatus('error'); return; }

            // Pickup marker — navy dot
            markersRef.current.push(new (window as any).google.maps.Marker({
                position: pickupLoc, map,
                title: 'Pickup: ' + order.pickup,
                icon: { path: (window as any).google.maps.SymbolPath.CIRCLE, scale: 10, fillColor: '#1B2A4A', fillOpacity: 1, strokeColor: '#fff', strokeWeight: 3 },
                label: { text: '📦', fontSize: '16px' }
            }));

            // Dropoff marker — green dot
            markersRef.current.push(new (window as any).google.maps.Marker({
                position: dropoffLoc, map,
                title: 'Dropoff: ' + order.dropoff,
                icon: { path: (window as any).google.maps.SymbolPath.CIRCLE, scale: 10, fillColor: '#10B981', fillOpacity: 1, strokeColor: '#fff', strokeWeight: 3 },
                label: { text: '🏠', fontSize: '16px' }
            }));

            // Rider marker — gold dot (only if GPS available)
            if (rider && rider.lat && rider.lng) {
                markersRef.current.push(new (window as any).google.maps.Marker({
                    position: { lat: rider.lat, lng: rider.lng }, map,
                    title: 'Rider: ' + (rider.name || 'Rider'),
                    icon: { path: (window as any).google.maps.SymbolPath.CIRCLE, scale: 12, fillColor: '#E8A838', fillOpacity: 1, strokeColor: '#fff', strokeWeight: 3 },
                    label: { text: '🏍️', fontSize: '16px' }
                }));
            }

            // Draw route
            new (window as any).google.maps.DirectionsService().route({
                origin: pickupLoc,
                destination: dropoffLoc,
                travelMode: (window as any).google.maps.TravelMode.DRIVING,
            }, (result: any, status: any) => {
                if (status === 'OK') {
                    directionsRendererRef.current.setDirections(result);
                } else {
                    // Route failed — just fit bounds to markers
                    const bounds = new (window as any).google.maps.LatLngBounds();
                    bounds.extend(pickupLoc);
                    bounds.extend(dropoffLoc);
                    if (rider && rider.lat && rider.lng) bounds.extend({ lat: rider.lat, lng: rider.lng });
                    map.fitBounds(bounds, { padding: 40 });
                }
                setMapStatus('ready');
            });
        })().catch(err => { console.error('DeliveryRouteMap error:', err); setMapStatus('error'); });
    }, [mapReady, order.id, order.pickup, order.dropoff, rider?.id, rider?.lat, rider?.lng]);

    return (
        <div style={{ position: 'relative', borderRadius: 10, overflow: 'hidden', border: `1px solid ${S.border}` }}>
            <div ref={mapRef} style={{ height: 230, width: '100%' }} />
            {mapStatus === 'loading' && (
                <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#EEF2F7', gap: 8 }}>
                    <div style={{ fontSize: 24 }}>🗺️</div>
                    <div style={{ fontSize: 11, color: S.textMuted }}>Loading map…</div>
                </div>
            )}
            {mapStatus === 'error' && (
                <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#EEF2F7', gap: 6 }}>
                    <div style={{ fontSize: 24 }}>📍</div>
                    <div style={{ fontSize: 11, color: S.textMuted }}>Could not load map</div>
                    <div style={{ fontSize: 10, color: S.textMuted }}>Check addresses or connection</div>
                </div>
            )}
        </div>
    );
}
