import './globals.css'
import { Outfit } from 'next/font/google'
import { AuthProvider } from '@/contexts/AuthContext'

const outfit = Outfit({ subsets: ['latin'] })

export const metadata = {
  title: 'Assured Express Merchant Portal',
  description: 'Manage your deliveries and wallet.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  console.log(process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY);
  return (
    <html lang="en">
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              function initMap() {
                console.log('🗺️ Google Maps loaded via callback');
                window.googleMapsLoaded = true;
                window.dispatchEvent(new Event('google-maps-loaded'));
              }
            `,
          }}
        />
        <script
          src={`https://maps.googleapis.com/maps/api/js?key=${process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY}&libraries=places&callback=initMap`}
          async
          defer
        ></script>
        <script src="https://js.paystack.co/v1/inline.js" async defer></script>
      </head>
      <body className={outfit.className}>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  )
}
