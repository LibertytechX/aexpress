import '@/globals.css';
import { DispatcherProvider } from '@/contexts/DispatcherContext';
import React from 'react';
import { GoogleMapsLoader } from '@/components/common/GoogleMapsLoader';

export const metadata = {
    title: 'AX Dispatch Portal v2.0',
    description: 'Manage riders, orders, and dispatch operations.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
    const gmKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
    return (
        <html lang="en">
            <body>
                <DispatcherProvider>
                    {children}
                </DispatcherProvider>
                {gmKey && <GoogleMapsLoader apiKey={gmKey} />}
            </body>
        </html>
    );
}
