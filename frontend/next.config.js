/** @type {import('next').NextConfig} */
const path = require('path');

const nextConfig = {
  reactStrictMode: true,
  // Ensure Turbopack uses frontend as project root (fixes "workspace root" error)
  turbopack: {
    root: path.join(__dirname),
  },
};

module.exports = nextConfig;
