import { useRef, useState, useEffect } from "react";
import { S } from "../common/theme";

// ─── RELAY NETWORK MAP (Google Maps: zones + relay nodes) ───────
export function RelayNetworkMap({ zones = [], relayNodes = [], height = 360 }: any) {
    const mapRef = useRef<HTMLDivElement>(null);
    const mapInstanceRef = useRef<any>(null);
    const markersRef = useRef<any[]>([]);
    const circlesRef = useRef<any[]>([]);
    const labelOverlaysRef = useRef<any[]>([]);
    const LabelOverlayCtorRef = useRef<any>(null);
    const infoWindowRef = useRef<any>(null);
    const [mapStatus, setMapStatus] = useState('loading');
    const [mapReady, setMapReady] = useState(false);

    const num = (v: any) => {
        const n = parseFloat(v);
        return Number.isFinite(n) ? n : null;
    };

    const clearOverlays = () => {
        markersRef.current.forEach(m => m.setMap(null));
        markersRef.current = [];
        circlesRef.current.forEach(c => c.setMap(null));
        circlesRef.current = [];
        labelOverlaysRef.current.forEach(o => o.setMap(null));
        labelOverlaysRef.current = [];
    };

    // Effect 1: Initialize the Google Map (once)
    useEffect(() => {
        const initializeMap = () => {
            if (!mapRef.current || mapInstanceRef.current) return;
            if (!(window as any).google || !(window as any).google.maps) { setMapStatus('error'); return; }

            const map = new (window as any).google.maps.Map(mapRef.current, {
                center: { lat: 6.5244, lng: 3.3792 },
                zoom: 11,
                mapTypeControl: false,
                streetViewControl: false,
                fullscreenControl: true,
                zoomControl: true,
                styles: [{ featureType: "poi", elementType: "labels", stylers: [{ visibility: "off" }] }]
            });

            mapInstanceRef.current = map;
            setMapReady(true);
            setMapStatus('ready');
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
            clearOverlays();
            if (infoWindowRef.current) { infoWindowRef.current.close(); infoWindowRef.current = null; }
            mapInstanceRef.current = null;
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Effect 2: Render zones + nodes whenever data changes
    useEffect(() => {
        if (!mapReady || !mapInstanceRef.current || !(window as any).google || !(window as any).google.maps) return;
        const map = mapInstanceRef.current;

        clearOverlays();
        if (!infoWindowRef.current) infoWindowRef.current = new (window as any).google.maps.InfoWindow();

        // Build (once) an OverlayView-based label that supports proper "pill/card" styling.
        if (!LabelOverlayCtorRef.current) {
            const g = (window as any).google.maps;
            LabelOverlayCtorRef.current = class MapLabelOverlay extends g.OverlayView {
                position: any;
                text: string;
                opts: any;
                div: HTMLDivElement | null;

                constructor(position: any, text: string, opts: any = {}) {
                    super();
                    this.position = position;
                    this.text = text;
                    this.opts = opts;
                    this.div = null;
                }
                onAdd() {
                    const div = document.createElement('div');
                    div.style.position = 'absolute';
                    div.style.pointerEvents = 'none';
                    div.style.userSelect = 'none';
                    div.style.whiteSpace = 'nowrap';
                    div.style.maxWidth = this.opts.maxWidth || '190px';
                    div.style.overflow = 'hidden';
                    div.style.textOverflow = 'ellipsis';

                    // Professional label styling (Google/Uber-like)
                    div.style.background = this.opts.background || 'rgba(255,255,255,0.90)';
                    div.style.border = this.opts.border || '1px solid rgba(15,23,42,0.12)';
                    div.style.borderRadius = this.opts.borderRadius || '999px';
                    div.style.padding = this.opts.padding || '5px 8px';
                    div.style.boxShadow = this.opts.boxShadow || '0 2px 6px rgba(0,0,0,0.18)';
                    div.style.backdropFilter = this.opts.backdropFilter || 'blur(2px)';

                    div.style.color = this.opts.color || '#1B2A4A';
                    div.style.fontSize = this.opts.fontSize || '12px';
                    div.style.fontWeight = this.opts.fontWeight || '700';
                    div.style.lineHeight = '1.1';
                    div.style.letterSpacing = '0.1px';

                    if (typeof this.opts.zIndex === 'number') div.style.zIndex = String(this.opts.zIndex);

                    div.textContent = this.text;
                    this.div = div;

                    const panes = this.getPanes();
                    // floatPane keeps labels above circles/tiles; still non-interactive.
                    (panes.floatPane || panes.overlayLayer).appendChild(div);
                }
                draw() {
                    if (!this.div) return;
                    const projection = this.getProjection();
                    if (!projection) return;
                    const pt = projection.fromLatLngToDivPixel(this.position);
                    if (!pt) return;
                    const ox = this.opts.offsetX || 0;
                    const oy = this.opts.offsetY || 0;
                    this.div.style.left = (pt.x + ox) + 'px';
                    this.div.style.top = (pt.y + oy) + 'px';

                    const anchor = this.opts.anchor || 'top';
                    if (anchor === 'center') this.div.style.transform = 'translate(-50%, -50%)';
                    else if (anchor === 'bottom') this.div.style.transform = 'translate(-50%, 0%)';
                    else this.div.style.transform = 'translate(-50%, -115%)'; // top (above point)
                }
                onRemove() {
                    if (this.div && this.div.parentNode) this.div.parentNode.removeChild(this.div);
                    this.div = null;
                }
            };
        }
        const MapLabelOverlay = LabelOverlayCtorRef.current;

        const bounds = new (window as any).google.maps.LatLngBounds();
        let hasAny = false;
        const palette = [S.blue, S.gold, S.green, S.purple, S.red];
        const zoneColorById: Record<string, string> = {};

        // Zones are used for color-coding nodes. We intentionally do NOT render
        // zone labels or zone radius circles to keep the map clean.
        (Array.isArray(zones) ? zones : []).forEach((z: any, idx: number) => {
            if (z && z.id != null) zoneColorById[String(z.id)] = palette[idx % palette.length];
            // Still extend bounds to keep the map centered around configured zones.
            const lat = num(z.center_lat);
            const lng = num(z.center_lng);
            if (lat == null || lng == null) return;
            bounds.extend({ lat, lng });
            hasAny = true;
        });

        (Array.isArray(relayNodes) ? relayNodes : []).forEach((n: any) => {
            const lat = num(n.latitude);
            const lng = num(n.longitude);
            if (lat == null || lng == null) return;
            const nodeName = (n.name || 'Relay Node').toString();
            const zoneId = (n && n.zone != null) ? String(n.zone) : null;
            const color = (zoneId && zoneColorById[zoneId]) ? zoneColorById[zoneId] : S.purple;

            // Relay node catchment radius (visual)
            const crkm = num(n.catchment_radius_km);
            if (crkm != null && crkm > 0) {
                const nodeCircle = new (window as any).google.maps.Circle({
                    map,
                    center: { lat, lng },
                    radius: crkm * 1000,
                    strokeColor: color,
                    strokeOpacity: 0.55,
                    strokeWeight: 1,
                    fillColor: color,
                    fillOpacity: 0.08,
                    clickable: false,
                });
                circlesRef.current.push(nodeCircle);
                const nb = nodeCircle.getBounds();
                if (nb) bounds.union(nb);
            }

            const marker = new (window as any).google.maps.Marker({
                map,
                position: { lat, lng },
                title: nodeName,
                icon: {
                    path: (window as any).google.maps.SymbolPath.CIRCLE,
                    scale: 8,
                    fillColor: color,
                    fillOpacity: 1,
                    strokeColor: '#fff',
                    strokeWeight: 3,
                },
            });
            markersRef.current.push(marker);
            bounds.extend({ lat, lng });
            hasAny = true;

            // Always-on styled node label (OverlayView), positioned above the marker
            const nodeLabel = new MapLabelOverlay(
                new (window as any).google.maps.LatLng(lat, lng),
                nodeName,
                {
                    anchor: 'top',
                    offsetY: -12,
                    fontSize: '11px',
                    fontWeight: '800',
                    padding: '5px 8px',
                    borderRadius: '999px',
                    zIndex: 1001,
                }
            );
            nodeLabel.setMap(map);
            labelOverlaysRef.current.push(nodeLabel);

            marker.addListener('click', () => {
                const title = n.name || 'Relay Node';
                const addr = n.address ? `<div style="opacity:0.8;margin-top:4px">${n.address}</div>` : '';
                const zone = n.zone_name ? `<div style="opacity:0.8;margin-top:4px">Zone: ${n.zone_name}</div>` : '';
                infoWindowRef.current.setContent(`<div style="font-size:12px"><b>${title}</b>${addr}${zone}</div>`);
                infoWindowRef.current.open({ map, anchor: marker });
            });
        });

        if (hasAny) {
            map.fitBounds(bounds, { padding: 50 });
            const z = map.getZoom?.();
            if (typeof z === 'number' && z > 16) map.setZoom(16);
        } else {
            map.setCenter({ lat: 6.5244, lng: 3.3792 });
            map.setZoom(11);
        }
        setMapStatus('ready');
    }, [mapReady, zones, relayNodes]);

    return (
        <div style={{ position: 'relative', borderRadius: 14, overflow: 'hidden', border: `1px solid ${S.border}`, background: '#EEF2F7' }}>
            <div ref={mapRef} style={{ height, width: '100%' }} />
            {mapStatus === 'loading' && (
                <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#EEF2F7', gap: 8 }}>
                    <div style={{ fontSize: 24 }}>🗺️</div>
                    <div style={{ fontSize: 11, color: S.textMuted }}>Loading map…</div>
                </div>
            )}
            {mapStatus === 'error' && (
                <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#EEF2F7', gap: 6 }}>
                    <div style={{ fontSize: 24 }}>📍</div>
                    <div style={{ fontSize: 11, color: S.textMuted }}>Google Maps not available</div>
                    <div style={{ fontSize: 10, color: S.textMuted }}>Check API key / network</div>
                </div>
            )}
        </div>
    );
}
