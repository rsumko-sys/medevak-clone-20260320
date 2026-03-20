import './globals.css'
import ClientLayout from '@/components/ClientLayout'

export const metadata = {
  title: 'Медичний модуль АЗОВ',
  description: 'АЗОВ • МЕДИЧНА СЛУЖБА • CCRM',
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
