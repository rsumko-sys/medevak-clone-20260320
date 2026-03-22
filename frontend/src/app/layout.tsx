import './globals.css'
import ClientLayout from '@/components/ClientLayout'

export const metadata = {
  title: 'CCRM • АЗОВ',
  description: 'АЗОВ • МЕДИЧНИЙ ПІДРОЗДІЛ',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="uk">
      <body>
        <ClientLayout>{children}</ClientLayout>
      </body>
    </html>
  )
}
