'use client';
// Map where a resident marks the problem: tap the map, drag the pin, or use the phone's location.
import {useEffect, useRef, useState} from 'react';
import 'leaflet/dist/leaflet.css';
import {tx, useLang} from '@/lib/i18n';
import {instance} from '@/lib/instance';

export type Picked = {lat: number; lng: number; accuracy?: number};

export default function LocationPicker({value, onChange}: {value: Picked | null; onChange: (p: Picked) => void}) {
  useLang();
  const box = useRef<HTMLDivElement>(null);
  const lib = useRef<any>(null), map = useRef<any>(null), pin = useRef<any>(null);
  const changeRef = useRef(onChange); changeRef.current = onChange;
  const [ready, setReady] = useState(false);
  const [locating, setLocating] = useState(false);
  const [geoError, setGeoError] = useState('');

  useEffect(() => {
    let dead = false;
    (async () => {
      const mod: any = await import('leaflet');
      const L: any = mod.default || mod;
      if (dead || !box.current) return;
      lib.current = L;
      const m = L.map(box.current, {scrollWheelZoom: false, tap: true}).setView([instance.mapCenter.lat, instance.mapCenter.lng], instance.id === 'rs' ? 7 : 11);
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors', referrerPolicy: 'strict-origin-when-cross-origin'}).addTo(m);
      m.on('click', (e: any) => changeRef.current({lat: e.latlng.lat, lng: e.latlng.lng, accuracy: 15}));
      map.current = m;
      setReady(true);
      setTimeout(() => m.invalidateSize(), 150);
    })();
    return () => { dead = true; map.current?.remove(); map.current = null; };
  }, []);

  // Keep the pin in sync with the chosen location.
  useEffect(() => {
    const L = lib.current, m = map.current;
    if (!ready || !L || !m) return;
    if (!value) { pin.current?.remove(); pin.current = null; return; }
    if (!pin.current) {
      const icon = L.divIcon({className: 'pick-pin', html: '<span></span>', iconSize: [28, 28], iconAnchor: [14, 28]});
      pin.current = L.marker([value.lat, value.lng], {draggable: true, icon, keyboard: true, title: tx('Problem location')}).addTo(m);
      pin.current.on('dragend', () => { const p = pin.current.getLatLng(); changeRef.current({lat: p.lat, lng: p.lng, accuracy: 10}); });
    } else pin.current.setLatLng([value.lat, value.lng]);
    if (m.getZoom() < 15) m.setView([value.lat, value.lng], 17);
  }, [value, ready]);

  const locate = () => {
    if (!navigator.geolocation) { setGeoError(tx('This device cannot share its location. Tap the map instead.')); return; }
    setLocating(true); setGeoError('');
    navigator.geolocation.getCurrentPosition(
      p => { setLocating(false); changeRef.current({lat: p.coords.latitude, lng: p.coords.longitude, accuracy: Math.round(p.coords.accuracy)}); },
      () => { setLocating(false); setGeoError(tx('Your location could not be found. Allow location access, or tap the map instead.')); },
      {enableHighAccuracy: true, timeout: 12000, maximumAge: 30000},
    );
  };

  return <div className="picker">
    <div className="picker-bar">
      <button type="button" className="secondary" onClick={locate} disabled={locating}>{locating ? tx('Finding your location…') : tx('Use my location')}</button>
      <span>{value ? tx('Pin placed. Drag it to adjust.') : tx('Or tap the map where the problem is.')}</span>
    </div>
    {geoError && <p className="form-error" role="alert">{geoError}</p>}
    <div ref={box} className="picker-map" role="application" aria-label={tx('Map: tap to mark the problem location')}/>
    {value && <small className="muted">{value.lat.toFixed(6)}, {value.lng.toFixed(6)}{value.accuracy ? ' · ±' + value.accuracy + ' m' : ''}</small>}
  </div>;
}
