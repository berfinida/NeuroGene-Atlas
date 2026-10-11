import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "NeuroGene Atlas", description: "GSE156496 transcriptomics research workspace" };
export default function Layout({children}: Readonly<{children: React.ReactNode}>) {
  return <html lang="en"><body>{children}</body></html>;
}
