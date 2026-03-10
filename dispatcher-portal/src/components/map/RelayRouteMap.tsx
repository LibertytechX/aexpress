import { useRef, useState, useEffect } from "react";
import { S } from "../common/theme";

// ─── RELAY ROUTE MAP (Google Maps: multi-hop relay legs) ────────
export function RelayRouteMap({ order, riders }: any) {
    const mapRef = useRef<HTMLDivElement>(null);
    const mapInstanceRef = useRef<any>(null);
    const markersRef = useRef<any[]>([]);
    const rendererRef = useRef<any>(null);
    const [mapStatus, setMapStatus] = useState('loading');
    const [mapReady, setMapReady] = useState(false);

    // Effect 1: Initialize map (once)
    useEffect(() => {
        const init = () => {
            if (!mapRef.current || mapInstanceRef.current) return;
            if (!(window as any).google || !(window as any).google.maps) { setMapStatus('error'); return; }
            const map = new (window as any).google.maps.Map(mapRef.current, {
                center: { lat: 6.5244, lng: 3.3792 }, zoom: 11,
                mapTypeControl: false, streetViewControl: false, fullscreenControl: true, zoomControl: true,
                styles: [{ featureType: "poi", elementType: "labels", stylers: [{ visibility: "off" }] }]
            });
            mapInstanceRef.current = map;
            rendererRef.current = new (window as any).google.maps.DirectionsRenderer({
                map, suppressMarkers: true,
                polylineOptions: {
                    strokeColor: '#3B82F6', strokeWeight: 4, strokeOpacity: 0.75,
                    icons: [{ icon: { path: (window as any).google.maps.SymbolPath.FORWARD_CLOSED_ARROW, scale: 3 }, offset: '50%', repeat: '80px' }]
                }
            });
            setMapReady(true);
        };
        let unsub: any = null;
        if ((window as any).google && (window as any).google.maps) { init(); }
        else { window.addEventListener('google-maps-loaded', init); unsub = () => window.removeEventListener('google-maps-loaded', init); }
        return () => {
            if (unsub) unsub();
            markersRef.current.forEach(m => m.setMap(null)); markersRef.current = [];
            if (rendererRef.current) { rendererRef.current.setMap(null); rendererRef.current = null; }
            mapInstanceRef.current = null;
        };
    }, []);

    // Effect 2: Draw relay route whenever legs change
    useEffect(() => {
        if (!mapReady || !mapInstanceRef.current || !(window as any).google) return;
        if (!order.relayLegs || order.relayLegs.length === 0) return;
        const map = mapInstanceRef.current;
        const geocoder = new (window as any).google.maps.Geocoder();
        const geocodeAddr = (addr: string) => new Promise((resolve) => {
            geocoder.geocode({ address: addr + ', Lagos, Nigeria' }, (results: any, status: any) => {
                resolve((status === 'OK' && results[0]) ? results[0].geometry.location : null);
            });
        });
        (async () => {
            markersRef.current.forEach(m => m.setMap(null)); markersRef.current = [];
            if (rendererRef.current) rendererRef.current.setDirections({ routes: [] });

            // Resolve pickup coordinates
            const pickupLoc = (order.pickupLat && order.pickupLng)
                ? new (window as any).google.maps.LatLng(parseFloat(order.pickupLat), parseFloat(order.pickupLng))
                : await geocodeAddr(order.pickup);
            if (!pickupLoc) { setMapStatus('error'); return; }

            // Resolve dropoff coordinates
            const dropoffLoc = (order.dropoffLat && order.dropoffLng)
                ? new (window as any).google.maps.LatLng(parseFloat(order.dropoffLat), parseFloat(order.dropoffLng))
                : await geocodeAddr(order.dropoff);
            if (!dropoffLoc) { setMapStatus('error'); return; }

            // Extract intermediate relay nodes (end_relay_node of every leg except the last)
            const legs = order.relayLegs;
            const intermediateNodes: any[] = [];
            for (let i = 0; i < legs.length - 1; i++) {
                const node = legs[i].end_relay_node;
                if (node && node.latitude && node.longitude) {
                    intermediateNodes.push({ lat: parseFloat(node.latitude), lng: parseFloat(node.longitude), name: node.name });
                }
            }

            // Fit the map to all points
            const bounds = new (window as any).google.maps.LatLngBounds();
            bounds.extend(pickupLoc); bounds.extend(dropoffLoc);
            intermediateNodes.forEach(n => bounds.extend({ lat: n.lat, lng: n.lng }));
            map.fitBounds(bounds, { padding: 50 });

            // Draw route through all waypoints
            const waypoints = intermediateNodes.map(n => ({ location: new (window as any).google.maps.LatLng(n.lat, n.lng), stopover: true }));
            new (window as any).google.maps.DirectionsService().route({
                origin: pickupLoc, destination: dropoffLoc, waypoints,
                travelMode: (window as any).google.maps.TravelMode.DRIVING, optimizeWaypoints: false,
            }, (result: any, status: any) => {
                if (status === 'OK' && rendererRef.current) rendererRef.current.setDirections(result);
                setMapStatus('ready');
            });

            // Pickup marker (📦)
            markersRef.current.push(new (window as any).google.maps.Marker({
                position: pickupLoc, map, title: 'Pickup: ' + order.pickup, zIndex: 10,
                icon: { path: (window as any).google.maps.SymbolPath.CIRCLE, scale: 10, fillColor: '#1B2A4A', fillOpacity: 1, strokeColor: '#fff', strokeWeight: 3 },
                label: { text: '📦', fontSize: '16px' }
            }));

            // Numbered relay node markers (⬡ purple)
            intermediateNodes.forEach((n, i) => {
                markersRef.current.push(new (window as any).google.maps.Marker({
                    position: { lat: n.lat, lng: n.lng }, map, title: `Relay ${i + 1}: ${n.name}`, zIndex: 9,
                    icon: { path: (window as any).google.maps.SymbolPath.CIRCLE, scale: 11, fillColor: '#8B5CF6', fillOpacity: 1, strokeColor: '#fff', strokeWeight: 3 },
                    label: { text: String(i + 1), fontSize: '11px', color: '#fff', fontWeight: 'bold' }
                }));
            });

            // Dropoff marker (🏠)
            markersRef.current.push(new (window as any).google.maps.Marker({
                position: dropoffLoc, map, title: 'Dropoff: ' + order.dropoff, zIndex: 10,
                icon: { path: (window as any).google.maps.SymbolPath.CIRCLE, scale: 10, fillColor: '#10B981', fillOpacity: 1, strokeColor: '#fff', strokeWeight: 3 },
                label: { text: '🏠', fontSize: '16px' }
            }));

            // Rider marker (🏍️) — show suggested rider GPS if available
            if (order.suggestedRiderId && riders) {
                const riderObj = riders.find((r: any) => r.id === order.suggestedRiderId);
                if (riderObj && riderObj.lat && riderObj.lng) {
                    markersRef.current.push(new (window as any).google.maps.Marker({
                        position: { lat: riderObj.lat, lng: riderObj.lng }, map, zIndex: 11,
                        title: 'Rider: ' + (riderObj.name || 'Rider'),
                        icon: { path: (window as any).google.maps.SymbolPath.CIRCLE, scale: 12, fillColor: '#E8A838', fillOpacity: 1, strokeColor: '#fff', strokeWeight: 3 },
                        label: { text: '🏍️', fontSize: '16px' }
                    }));
                }
            }
        })().catch(err => { console.error('RelayRouteMap error:', err); setMapStatus('error'); });
    }, [mapReady, order.id, order.relayLegs?.length, order.suggestedRiderId]);

    return (
        <div style={{ position: 'relative', borderRadius: 10, overflow: 'hidden', border: `1px solid ${S.border}` }}>
            <div ref={mapRef} style={{ height: 300, width: '100%' }} />
            {mapStatus === 'loading' && (
                <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#EEF2F7', gap: 8 }}>
                    <div style={{ fontSize: 24 }}>🗺️</div>
                    <div style={{ fontSize: 11, color: S.textMuted }}>Loading relay route…</div>
                </div>
            )}
            {mapStatus === 'error' && (
                <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#EEF2F7', gap: 6 }}>
                    <div style={{ fontSize: 24 }}>📍</div>
                    <div style={{ fontSize: 11, color: S.textMuted }}>Could not render relay route map</div>
                </div>
            )}
        </div>
    );
}
