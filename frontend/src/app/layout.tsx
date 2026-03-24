import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'CodePrompt Pro',
  description: 'AI-Powered Vibe Coding Assistant',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
