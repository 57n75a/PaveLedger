'use client';
import {useEffect} from 'react';
// Registers the service worker so the app can be installed and opened without a connection.
export default function SwRegister() {
  useEffect(() => {
    if (!('serviceWorker' in navigator) || process.env.NODE_ENV !== 'production') return;
    const go = () => navigator.serviceWorker.register('/sw.js', {scope: '/'}).catch(() => {});
    if (document.readyState === 'complete') go(); else window.addEventListener('load', go, {once: true});
  }, []);
  return null;
}
