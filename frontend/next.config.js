/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  env: {
    // Browser-seitige API Base URL (muss vom Host erreichbar sein, z.B. http://localhost:8000)
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  },
  async rewrites() {
    // Server-seitige Rewrite-Target URL (läuft im Container; kann Compose-DNS nutzen, z.B. http://backend:8000)
    const publicBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
    const internalBaseUrl = process.env.INTERNAL_API_BASE_URL || publicBaseUrl

    return [
      {
        source: '/api/:path*',
        destination: `${internalBaseUrl}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
