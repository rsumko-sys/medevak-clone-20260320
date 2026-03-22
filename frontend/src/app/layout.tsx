import './globals.css'
import { Inter } from 'next/font/google'
import ClientLayout from '@/components/ClientLayout'

const inter = Inter({
  subsets: ['latin', 'cyrillic'],
  variable: '--app-font-family',
  display: 'swap',
})

export const metadata = {
  title: 'CCRM • АЗОВ',
  description: 'АЗОВ • МЕДИЧНИЙ ПІДРОЗДІЛ',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="uk" className={inter.variable}>
      <body>
        <ClientLayout>{children}</ClientLayout>
      </body>
    </html>
  )
}
