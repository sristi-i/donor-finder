import "./globals.css";

export const metadata = { title: "Donor Finder" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900">
        <div className="container-page">{children}</div>
      </body>
    </html>
  );
}
