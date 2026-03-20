import './globals.css'
import ClientLayout from '@/components/ClientLayout'

export const metadata = {
  title: 'Медичний модуль Вовків Да Вінчі',
  description: 'ВОВКІВ ДА ВІНЧІ • МЕД СЛУЖБА УЛЬФ',
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
