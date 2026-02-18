import './globals.css'
import { Outfit } from 'next/font/google'
import { AuthProvider } from '@/contexts/AuthContext'

const outfit = Outfit({ subsets: ['latin'] })

export const metadata = {
  title: 'Assured Express Merchant Portal',
  description: 'Manage your deliveries and wallet',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <script
          src={`https://maps.googleapis.com/maps/api/js?key=AIzaSyD-xxxxxxxxxxxxxxxxxxxxxxxxxxxx&libraries=places`}
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
