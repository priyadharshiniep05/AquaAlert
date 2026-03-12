const MAP_STYLE = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';

function initMap(elementId, lat = 19.0760, lng = 72.8777) {
  const map = L.map(elementId, {
    zoomControl: false
  }).setView([lat, lng], 13);
  
  L.control.zoom({ position: 'bottomright' }).addTo(map);
  
  L.tileLayer(MAP_STYLE, {
    attribution: '&copy; <a href="https://carto.com/">CartoDB</a>',
    subdomains: 'abcd',
    maxZoom: 20
  }).addTo(map);

  // User location marker
  const pulseIcon = L.divIcon({
    className: 'pulse-icon',
    html: '<div style="background:#00D4FF;width:12px;height:12px;border-radius:50%;box-shadow:0 0 10px #00D4FF, 0 0 0 5px rgba(0,212,255,0.3)"></div>',
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  });
  L.marker([lat, lng], {icon: pulseIcon}).addTo(map).bindPopup("<b>You are here</b>");

  return map;
}

async function loadFloodZones(map) {
  try {
    const zones = await fetch('/api/flood-zones').then(r => r.json());
    const layers = [];
    zones.forEach(z => {
      let color, fillOpacity;
      if (z.risk === 'HIGH') { color = '#FF3B3B'; fillOpacity = 0.4; }
      else if (z.risk === 'MEDIUM') { color = '#FF8C00'; fillOpacity = 0.3; }
      else { color = '#FFFF00'; fillOpacity = 0.2; }
      
      const circle = L.circle([z.lat, z.lng], {
        color: color,
        fillColor: color,
        fillOpacity: fillOpacity,
        radius: z.radius
      }).addTo(map);
      
      circle.bindPopup(`<b>${z.name}</b><br>Risk Level: ${z.risk}`);
      layers.push(circle);
    });
    return layers;
  } catch (e) {
    console.error("Error loading flood zones", e);
    return [];
  }
}

async function loadShelters(map) {
  try {
    let data;
    try {
      const res = await fetch('/api/shelters');
      data = await res.json();
    } catch(e) {
      data = [
        {"id": 1, "name": "Dharavi Relief Center", "lat": 19.0400, "lng": 72.8660, "capacity": 500, "type": "primary", "contact": "+91-22-24041234", "facilities": ["Water", "Food", "Medical", "Cots"]},
        {"id": 2, "name": "Sion Government School", "lat": 19.0440, "lng": 72.8633, "capacity": 300, "type": "secondary", "contact": "+91-22-24045678", "facilities": ["Water", "Food", "Cots"]},
        {"id": 3, "name": "BKC Sports Complex", "lat": 19.0653, "lng": 72.8647, "capacity": 1000, "type": "primary", "contact": "+91-22-26591234", "facilities": ["Water", "Food", "Medical", "Cots", "WiFi"]},
        {"id": 4, "name": "Kurla Municipal Hall", "lat": 19.0700, "lng": 72.8800, "capacity": 250, "type": "secondary", "contact": "+91-22-25010000", "facilities": ["Water", "Food"]},
        {"id": 5, "name": "Andheri Sports Club", "lat": 19.1136, "lng": 72.8397, "capacity": 400, "type": "primary", "contact": "+91-22-26831234", "facilities": ["Water", "Food", "Medical"]}
      ];
    }
    
    if (!data || data.length === 0) return [];

    const shelterIcon = L.divIcon({
      html: '🏠',
      className: 'shelter-marker-icon',
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    });
    
    const layers = [];
    data.forEach(s => {
      const m = L.marker([s.lat, s.lng], {icon: shelterIcon}).addTo(map);
      m.bindPopup(`
        <div style="color:black">
          <b>${s.name}</b><br>
          Capacity: ${s.capacity}<br>
          📞 <a href="tel:${s.contact}">${s.contact}</a>
        </div>
      `);
      layers.push(m);
    });
    return layers;
  } catch (e) {
    console.error("Error loading shelters", e);
    return [];
  }
}

async function loadCommunityReports(map) {
  try {
    const reports = await fetch('/api/reports').then(r => r.json());
    const layers = [];
    reports.forEach(r => {
      let iconHtml = '💧';
      if (r.severity === 'severe') iconHtml = '🚨';
      else if (r.severity === 'waterlogging') iconHtml = '⚠️';
      
      const repIcon = L.divIcon({
        html: `<div style="font-size: 20px; filter: drop-shadow(0px 2px 2px rgba(0,0,0,0.5));">${iconHtml}</div>`,
        className: 'report-marker',
        iconSize: [24, 24]
      });
      
      const m = L.marker([r.lat, r.lng], {icon: repIcon}).addTo(map);
      
      m.bindPopup(`
        <div style="color:black">
          <b>${r.severity.toUpperCase()}</b><br>
          ${r.description}<br>
          <small>${new Date(r.timestamp).toLocaleTimeString()}</small><br>
          👍 ${r.upvotes} · 👎 ${r.downvotes}
        </div>
      `);
      layers.push(m);
    });
    return layers;
  } catch (e) {
    console.error("Error loading reports", e);
    return [];
  }
}

async function loadSafeRoutes(map) {
  try {
    const routes = await fetch('/api/safe-routes').then(r => r.json());
    const layers = [];
    routes.forEach(r => {
      const polyline = L.polyline(r.waypoints, {
        color: '#00FF88',
        weight: 4,
        dashArray: '10, 10',
        lineCap: 'round',
        opacity: 0.8
      }).addTo(map);
      polyline.bindPopup(`Safe Route: ${r.name}`);
      layers.push(polyline);
    });
    return layers;
  } catch(e) {
    console.error(e);
    return [];
  }
}

async function loadSensorMarkers(map) {
  try {
    const sensors = await fetch('/api/sensors').then(r => r.json());
    sensors.forEach(s => {
      const color = s.water_level_cm > 100 ? 'red' : s.water_level_cm > 50 ? 'orange' : 'green';
      const circle = L.circleMarker([s.lat, s.lng], {
        radius: 6,
        fillColor: color,
        color: '#fff',
        weight: 1,
        opacity: 1,
        fillOpacity: 0.8
      }).addTo(map);
      circle.bindPopup(`<b>${s.name} Sensor</b><br>Level: ${s.water_level_cm}cm`);
    });
  } catch(e) {
    console.error(e);
  }
}
