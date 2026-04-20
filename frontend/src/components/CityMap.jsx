import React, { useEffect, useRef } from 'react';
import { gwaliorLocations } from '../mockData/gwaliorData';

const AQI_COLORS = (aqi) => {
  if (aqi <= 50)  return '#22c55e';
  if (aqi <= 100) return '#f59e0b';
  if (aqi <= 200) return '#ef4444';
  return '#a855f7';
};

const AQI_LABEL = (aqi) => {
  if (aqi <= 50)  return 'Good';
  if (aqi <= 100) return 'Moderate';
  if (aqi <= 200) return 'Poor';
  return 'Severe';
};

export default function CityMap({ dataMap, selectedLocationId }) {
  const mapRef    = useRef(null);
  const leafletMap = useRef(null);
  const markersRef = useRef([]);

  // Init map once
  useEffect(() => {
    if (leafletMap.current || !window.L) return;
    leafletMap.current = window.L.map(mapRef.current, { zoomControl: true }).setView([26.218, 78.183], 12);
    window.L.tileLayer(
      'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
      { attribution: '&copy; OpenStreetMap &copy; CARTO', maxZoom: 20 }
    ).addTo(leafletMap.current);
    return () => { leafletMap.current?.remove(); leafletMap.current = null; };
  }, []);

  // Update markers on data change
  useEffect(() => {
    if (!leafletMap.current || !window.L) return;
    markersRef.current.forEach(m => leafletMap.current.removeLayer(m));
    markersRef.current = [];

    gwaliorLocations.forEach(loc => {
      const locData = dataMap[loc.id];
      if (!locData?.length) return;

      const { aqi, temperature, humidity } = locData[0];
      const color   = AQI_COLORS(aqi);
      const isSelected = selectedLocationId === loc.id;

      const marker = window.L.circleMarker([loc.lat, loc.lng], {
        radius: isSelected ? 14 : 9,
        fillColor: color,
        color: isSelected ? '#0f172a' : '#ffffff',
        weight: isSelected ? 3 : 1.5,
        opacity: 1,
        fillOpacity: isSelected ? 1 : 0.82,
      }).addTo(leafletMap.current);

      marker.bindPopup(`
        <div style="font-family:Inter,sans-serif;min-width:140px;padding:4px">
          <div style="font-weight:700;font-size:13px;margin-bottom:6px">${loc.name}</div>
          <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px">
            <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${color}"></span>
            <span style="font-size:13px;font-weight:600">AQI ${Math.round(aqi)}</span>
            <span style="font-size:11px;color:#64748b">${AQI_LABEL(aqi)}</span>
          </div>
          <div style="font-size:11px;color:#64748b">${temperature?.toFixed(1)}°C &nbsp;·&nbsp; ${humidity?.toFixed(0)}% RH</div>
        </div>
      `, { maxWidth: 200 });

      marker.bindTooltip(loc.name, { direction: 'top', offset: [0, -12], className: '' });
      if (isSelected) marker.bringToFront();
      markersRef.current.push(marker);
    });
  }, [dataMap, selectedLocationId]);

  return (
    <div
      ref={mapRef}
      style={{ height: '100%', width: '100%', minHeight: 340, borderRadius: 'inherit' }}
    />
  );
}
