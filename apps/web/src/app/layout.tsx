import React from "react";

export const metadata = {
  title: "DERA — Database Engineering & Reverse Analysis",
  description: "Understand Every Schema. Engineer Every Change. Deterministic database reverse engineering platform.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}): React.ReactElement {
  return (
    <html lang="en">
      <body style={{ margin: 0, padding: 0 }}>
        {children}
      </body>
    </html>
  );
}
