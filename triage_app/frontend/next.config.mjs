/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static export: npm run build → out/ → có thể serve từ FastAPI
  output: process.env.NEXT_STANDALONE ? undefined : 'export',
  trailingSlash: true,
  images: { unoptimized: true },
};

export default nextConfig;
