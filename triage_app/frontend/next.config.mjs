/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static export: npm run build → out/ → FastAPI serve tại /app
  output: process.env.NEXT_STANDALONE ? undefined : 'export',
  trailingSlash: true,
  images: { unoptimized: true },
  // Khi serve từ /app, asset phải có prefix /app (tránh 404 cho /next/static/...)
  basePath: '/app',
  assetPrefix: '/app',
};

export default nextConfig;
