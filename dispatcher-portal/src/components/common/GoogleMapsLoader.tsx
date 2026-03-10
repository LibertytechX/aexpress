'use client';

import Script from 'next/script';

export function GoogleMapsLoader({ apiKey }: { apiKey: string }) {
    return (
        <Script
            id="google-maps"
            src={`https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places,geometry`}
            strategy="afterInteractive"
            onLoad={() => {
                window.dispatchEvent(new Event('google-maps-loaded'));
            }}
        />
    );
}
