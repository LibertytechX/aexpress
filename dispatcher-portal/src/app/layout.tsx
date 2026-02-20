import '@/globals.css';
import { DispatcherProvider } from '@/contexts/DispatcherContext';
import React from 'react';

export const metadata = {
    title: 'AX Dispatch Portal v2.0',
    description: 'Manage riders, orders, and dispatch operations.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en">
            <body>
                <DispatcherProvider>
                    {children}
                </DispatcherProvider>
            </body>
        </html>
    );
}
