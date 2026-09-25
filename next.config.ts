import type { NextConfig } from "next";
const nextConfig: NextConfig = {
  async headers() { return [{ source: '/(.*)', headers: [
    {key:'X-Content-Type-Options',value:'nosniff'},
    {key:'Referrer-Policy',value:'same-origin'},
    {key:'X-Frame-Options',value:'DENY'},
    {key:'Permissions-Policy',value:'geolocation=(self), camera=(self), microphone=()'}
  ]}]; }
};
export default nextConfig;
