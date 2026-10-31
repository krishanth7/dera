/**
 * DERA — Database Engineering & Reverse Analysis
 * Next.js Application Configuration — Phase 7.1
 *
 * Security headers, bundle optimization, and framework configuration.
 * Reference: https://nextjs.org/docs/app/api-reference/config/next-config-js
 */

import type { NextConfig } from "next";

/**
 * HTTP Security Headers applied to all responses.
 * Evaluated against Next.js App Router requirements.
 */
const securityHeaders = [
  {
    key: "X-DNS-Prefetch-Control",
    value: "on",
  },
  {
    key: "X-Content-Type-Options",
    value: "nosniff",
  },
  {
    key: "X-Frame-Options",
    value: "SAMEORIGIN",
  },
  {
    key: "X-XSS-Protection",
    value: "1; mode=block",
  },
  {
    key: "Referrer-Policy",
    value: "strict-origin-when-cross-origin",
  },
  {
    key: "Permissions-Policy",
    value: "camera=(), microphone=(), geolocation=(), interest-cohort=()",
  },
  /**
   * Content Security Policy.
   * 'unsafe-inline' for styles is required by Tailwind CSS v4's runtime approach.
   * 'unsafe-eval' is NOT permitted.
   * Adjust connect-src to include your production API domain.
   */
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline'",
      "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
      "font-src 'self' https://fonts.gstatic.com",
      "img-src 'self' data: blob:",
      "connect-src 'self' http://localhost:8000 https://localhost:8000",
      "frame-ancestors 'self'",
      "base-uri 'self'",
      "form-action 'self'",
      "object-src 'none'",
    ].join("; "),
  },
];

const nextConfig: NextConfig = {
  /**
   * Strict mode for additional React development-time checks.
   * Intentionally enabled — helps surface issues early.
   */
  reactStrictMode: true,

  /**
   * Apply security headers on all routes.
   */
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: securityHeaders,
      },
    ];
  },

  /**
   * Experimental features — none enabled in Phase 7.1.
   * typedRoutes would be beneficial but requires all routes to exist.
   */

  /**
   * Logging configuration.
   */
  logging: {
    fetches: {
      fullUrl: false,
    },
  },

  /**
   * Trusted origins for CSRF protection.
   * Extend for production deployment.
   */
  serverExternalPackages: [],

  /**
   * Image optimization configuration.
   * No external domains required in Phase 7.1.
   */
  images: {
    remotePatterns: [],
  },
};

export default nextConfig;
