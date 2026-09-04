import React, { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Contact, NavWaypoint } from '../../types/detection';
import { Layers, Compass, ZoomIn, ZoomOut, Maximize2, Anchor, Eye } from 'lucide-react';

interface MapViewProps {
  contacts: Contact[];
  selectedContact: Contact | null;
  navTrack: NavWaypoint[];
  onSelectContact: (contact: Contact) => void;
}

// Public, high-resolution tile sources with ZERO watermark & NO API KEY needed
const BASEMAP_STYLES = {
  satellite: {
    name: 'Maritime Satellite Imagery',
    tiles: [
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
    ],
    maxzoom: 19,
    attribution: '© Esri, Maxar, Earthstar Geographics'
  },
  bathymetry: {
    name: 'Nautical Ocean Bathymetry',
    tiles: [
      'https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}'
    ],
    maxzoom: 13,
    attribution: '© Esri, GEBCO, NOAA, National Geographic, Garmin'
  },
  osm: {
    name: 'OpenStreetMap Hydrographic',
    tiles: [
      'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
    ],
    maxzoom: 19,
    attribution: '© OpenStreetMap contributors'
  },
  dark_ocean: {
    name: 'Dark Canvas',
    tiles: [
      'https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}'
    ],
    maxzoom: 16,
    attribution: '© Esri, HERE, Garmin'
  }
};

type BasemapKey = keyof typeof BASEMAP_STYLES;

export const MapView: React.FC<MapViewProps> = ({
  contacts,
  selectedContact,
  navTrack,
  onSelectContact
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<{ [key: string]: maplibregl.Marker }>({});
  const [mapReady, setMapReady] = useState<boolean>(false);
  const [activeBasemap, setActiveBasemap] = useState<BasemapKey>('satellite');
  const [showLayerMenu, setShowLayerMenu] = useState<boolean>(false);
  const [showTrackline, setShowTrackline] = useState<boolean>(true);
  const [showTargets, setShowTargets] = useState<boolean>(true);

  // Default coordinate center (Baltic/North Sea or Coastal coordinates)
  const defaultCenter: [number, number] = [12.6789, 54.1234];

  // Initialize MapLibre
  useEffect(() => {
    if (!mapContainer.current || mapInstance.current) return;

    try {
      const initialStyle = BASEMAP_STYLES.satellite;
      const map = new maplibregl.Map({
        container: mapContainer.current,
        style: {
          version: 8,
          sources: {
            'basemap-source': {
              type: 'raster',
              tiles: initialStyle.tiles,
              tileSize: 256,
              maxzoom: initialStyle.maxzoom,
              attribution: initialStyle.attribution
            }
          },
          layers: [
            {
              id: 'basemap-layer',
              type: 'raster',
              source: 'basemap-source',
              minzoom: 0,
              maxzoom: 22
            }
          ]
        },
        center: defaultCenter,
        zoom: 15,
        attributionControl: false
      });

      map.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'top-right');
      map.addControl(new maplibregl.ScaleControl({ maxWidth: 150, unit: 'metric' }), 'bottom-left');

      map.on('load', () => {
        mapInstance.current = map;
        setMapReady(true);
      });

      return () => {
        map.remove();
        mapInstance.current = null;
      };
    } catch (err) {
      console.warn('MapLibre init error:', err);
    }
  }, []);

  // Switch basemap layer dynamically
  const handleSwitchBasemap = (key: BasemapKey) => {
    setActiveBasemap(key);
    setShowLayerMenu(false);
    if (!mapInstance.current || !mapReady) return;
    const map = mapInstance.current;
    const styleConf = BASEMAP_STYLES[key];

    map.setStyle({
      version: 8,
      sources: {
        'basemap-source': {
          type: 'raster',
          tiles: styleConf.tiles,
          tileSize: 256,
          maxzoom: styleConf.maxzoom,
          attribution: styleConf.attribution
        }
      },
      layers: [
        {
          id: 'basemap-layer',
          type: 'raster',
          source: 'basemap-source',
          minzoom: 0,
          maxzoom: 22
        }
      ]
    });
  };

  // Draw Towfish Trajectory Trackline & Waypoints
  useEffect(() => {
    if (!mapInstance.current || !mapReady) return;
    const map = mapInstance.current;

    const trackSourceId = 'towfish-track-source';
    const trackLayerId = 'towfish-track-line';
    const trackPointsId = 'towfish-track-points';

    // Remove existing layers/source if present
    if (map.getLayer(trackPointsId)) map.removeLayer(trackPointsId);
    if (map.getLayer(trackLayerId)) map.removeLayer(trackLayerId);
    if (map.getSource(trackSourceId)) map.removeSource(trackSourceId);

    if (!showTrackline || !navTrack || navTrack.length === 0) return;

    const coordinates = navTrack
      .filter(p => p.latitude != null && p.longitude != null)
      .map(p => [p.longitude, p.latitude]);

    if (coordinates.length === 0) return;

    const geojsonData: GeoJSON.FeatureCollection = {
      type: 'FeatureCollection',
      features: [
        {
          type: 'Feature',
          properties: {},
          geometry: {
            type: 'LineString',
            coordinates: coordinates
          }
        },
        ...navTrack.map((p) => ({
          type: 'Feature' as const,
          properties: {
            ping_id: p.ping_id,
            heading: p.heading
          },
          geometry: {
            type: 'Point' as const,
            coordinates: [p.longitude, p.latitude]
          }
        }))
      ]
    };

    map.addSource(trackSourceId, {
      type: 'geojson',
      data: geojsonData
    });

    // Glowing survey trackline
    map.addLayer({
      id: trackLayerId,
      type: 'line',
      source: trackSourceId,
      filter: ['==', '$type', 'LineString'],
      paint: {
        'line-color': '#00d2ff',
        'line-width': 3,
        'line-opacity': 0.85
      }
    });

    // Towfish ping waypoints
    map.addLayer({
      id: trackPointsId,
      type: 'circle',
      source: trackSourceId,
      filter: ['==', '$type', 'Point'],
      paint: {
        'circle-radius': 3.5,
        'circle-color': '#00d2ff',
        'circle-stroke-width': 1.5,
        'circle-stroke-color': '#ffffff'
      }
    });
  }, [navTrack, mapReady, showTrackline]);

  // Update Contact Markers with Interactive Popups & Pulsing Rings
  useEffect(() => {
    if (!mapInstance.current || !mapReady) return;
    const map = mapInstance.current;

    // Clear old markers
    Object.values(markersRef.current).forEach(m => m.remove());
    markersRef.current = {};

    if (!showTargets) return;

    const validContacts = contacts.filter(
      c => c.latitude != null && c.longitude != null
    );

    validContacts.forEach(contact => {
      const isSelected = selectedContact?.contact_id === contact.contact_id;
      const el = document.createElement('div');
      el.className = 'cursor-pointer select-none group relative';

      let bg = '#ff383c'; // Placely Vivid Red for High Priority
      let glow = '0 0 16px rgba(255, 56, 60, 0.9)';
      let ringColor = 'rgba(255, 56, 60, 0.4)';
      let pulseAnim = 'animate-ping';

      if (contact.priority === 'MEDIUM') {
        bg = '#ffd400';
        glow = '0 0 14px rgba(255, 212, 0, 0.9)';
        ringColor = 'rgba(255, 212, 0, 0.4)';
      } else if (contact.priority === 'LOW') {
        bg = '#00d2ff';
        glow = '0 0 10px rgba(0, 210, 255, 0.7)';
        ringColor = 'rgba(0, 210, 255, 0.3)';
        pulseAnim = '';
      }

      el.innerHTML = `
        <div style="position: relative; display: flex; align-items: center; justify-content: center;">
          ${isSelected || contact.priority === 'HIGH' ? `
            <div style="
              position: absolute;
              width: 38px;
              height: 38px;
              border-radius: 50%;
              background-color: ${ringColor};
              animation: ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;
            "></div>
          ` : ''}
          <div style="
            position: relative;
            background-color: ${bg};
            width: ${isSelected ? '30px' : '24px'};
            height: ${isSelected ? '30px' : '24px'};
            border-radius: 50%;
            border: 2.5px solid #ffffff;
            box-shadow: ${glow};
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'JetBrains Mono', monospace;
            font-size: ${isSelected ? '10px' : '9px'};
            font-weight: 800;
            color: ${contact.priority === 'MEDIUM' ? '#1f1f1f' : '#ffffff'};
            transition: all 0.2s ease-in-out;
          ">
            ${contact.contact_id}
          </div>
        </div>
      `;

      // Interactive Popup
      const popup = new maplibregl.Popup({ offset: 25, closeButton: false })
        .setHTML(`
          <div style="
            padding: 10px 14px;
            font-family: 'Inter', sans-serif;
            background: #ffffff;
            border-radius: 12px;
            border: 1px solid #e6e6e6;
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1);
          ">
            <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 4px;">
              <span style="font-weight: 800; font-size: 13px; color: #1f1f1f;">${contact.contact_id}</span>
              <span style="
                font-size: 10px;
                font-weight: 700;
                padding: 2px 6px;
                border-radius: 9999px;
                background-color: ${contact.priority === 'HIGH' ? '#fef2f2' : '#fffbeb'};
                color: ${contact.priority === 'HIGH' ? '#dc2626' : '#d97706'};
              ">${contact.priority}</span>
            </div>
            <div style="font-size: 11px; color: #64748b; margin-bottom: 2px;">
              Target: <strong style="color: #1f1f1f;">${contact.class_name.replace('_', ' ').toUpperCase()}</strong>
            </div>
            <div style="font-size: 11px; color: #64748b; margin-bottom: 4px;">
              Confidence: <strong style="color: #10b981;">${(contact.confidence * 100).toFixed(1)}%</strong>
            </div>
            <div style="font-size: 10px; font-family: 'JetBrains Mono', monospace; color: #8e8e93; border-top: 1px solid #f1f5f9; padding-top: 4px;">
              ${contact.latitude?.toFixed(5)}°N, ${contact.longitude?.toFixed(5)}°E
            </div>
          </div>
        `);

      el.addEventListener('click', () => {
        onSelectContact(contact);
      });

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([contact.longitude!, contact.latitude!])
        .setPopup(popup)
        .addTo(map);

      markersRef.current[contact.contact_id] = marker;
    });

    // Automatically fit bounds if we have valid coordinates
    if (validContacts.length > 0) {
      const bounds = new maplibregl.LngLatBounds();
      validContacts.forEach(c => bounds.extend([c.longitude!, c.latitude!]));
      if (navTrack && navTrack.length > 0) {
        navTrack.forEach(p => {
          if (p.latitude != null && p.longitude != null) {
            bounds.extend([p.longitude, p.latitude]);
          }
        });
      }
      map.fitBounds(bounds, { padding: 80, maxZoom: 16, duration: 1000 });
    }
  }, [contacts, selectedContact, mapReady, onSelectContact, showTargets, navTrack]);

  // Center map on selected contact
  useEffect(() => {
    if (!mapInstance.current || !selectedContact) return;
    if (selectedContact.longitude != null && selectedContact.latitude != null) {
      mapInstance.current.flyTo({
        center: [selectedContact.longitude, selectedContact.latitude],
        zoom: 16,
        essential: true,
        speed: 1.4
      });
    }
  }, [selectedContact]);

  const handleRecenter = () => {
    if (!mapInstance.current) return;
    const validContacts = contacts.filter(c => c.latitude != null && c.longitude != null);
    if (validContacts.length > 0) {
      const bounds = new maplibregl.LngLatBounds();
      validContacts.forEach(c => bounds.extend([c.longitude!, c.latitude!]));
      if (navTrack && navTrack.length > 0) {
        navTrack.forEach(p => {
          if (p.latitude != null && p.longitude != null) {
            bounds.extend([p.longitude, p.latitude]);
          }
        });
      }
      mapInstance.current.fitBounds(bounds, { padding: 80, maxZoom: 16, duration: 1000 });
    }
  };

  return (
    <div className="w-full h-full relative overflow-hidden rounded-[20px] border border-[#e6e6e6] bg-[#0c121e]">
      <div ref={mapContainer} className="w-full h-full" />

      {/* Top Left: Basemap Switcher & Layer Controls */}
      <div className="absolute top-4 left-4 z-20 flex items-center gap-2">
        <div className="relative">
          <button
            onClick={() => setShowLayerMenu(!showLayerMenu)}
            className="h-9 px-3.5 rounded-full bg-white/95 backdrop-blur shadow-tactile border border-[#e6e6e6] text-[#1f1f1f] text-xs font-semibold flex items-center gap-2 hover:bg-slate-50 transition-all cursor-pointer"
          >
            <Layers className="w-4 h-4 text-[#ff383c]" />
            <span>{BASEMAP_STYLES[activeBasemap].name}</span>
          </button>

          {showLayerMenu && (
            <div className="absolute top-11 left-0 w-60 bg-white rounded-2xl border border-[#e6e6e6] shadow-xl p-2 z-30 space-y-1 font-sans">
              <div className="text-[10px] font-bold text-[#8e8e93] uppercase tracking-wider px-2 py-1">
                Nautical Chart Style
              </div>
              {(Object.keys(BASEMAP_STYLES) as BasemapKey[]).map((key) => (
                <button
                  key={key}
                  onClick={() => handleSwitchBasemap(key)}
                  className={`w-full text-left px-3 py-2 rounded-xl text-xs font-semibold flex items-center justify-between transition-colors cursor-pointer ${
                    activeBasemap === key ? 'bg-[#ff383c]/10 text-[#ff383c]' : 'text-[#1f1f1f] hover:bg-slate-50'
                  }`}
                >
                  <span>{BASEMAP_STYLES[key].name}</span>
                  {activeBasemap === key && <span className="w-2 h-2 rounded-full bg-[#ff383c]" />}
                </button>
              ))}

              <div className="border-t border-slate-100 my-1 pt-1">
                <div className="text-[10px] font-bold text-[#8e8e93] uppercase tracking-wider px-2 py-1">
                  Overlay Layers
                </div>
                <button
                  onClick={() => setShowTrackline(!showTrackline)}
                  className="w-full text-left px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center justify-between hover:bg-slate-50 text-[#1f1f1f] cursor-pointer"
                >
                  <span className="flex items-center gap-2">
                    <span className="w-2.5 h-0.5 bg-[#00d2ff] rounded-full inline-block" />
                    Towfish Trajectory
                  </span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${showTrackline ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>
                    {showTrackline ? 'ON' : 'OFF'}
                  </span>
                </button>
                <button
                  onClick={() => setShowTargets(!showTargets)}
                  className="w-full text-left px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center justify-between hover:bg-slate-50 text-[#1f1f1f] cursor-pointer"
                >
                  <span className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-[#ff383c] rounded-full inline-block" />
                    Anomaly Targets
                  </span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${showTargets ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>
                    {showTargets ? 'ON' : 'OFF'}
                  </span>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Recenter button */}
        <button
          onClick={handleRecenter}
          title="Fit bounds to survey swath & targets"
          className="h-9 px-3 rounded-full bg-white/95 backdrop-blur shadow-tactile border border-[#e6e6e6] text-[#1f1f1f] text-xs font-semibold flex items-center gap-1.5 hover:bg-slate-50 transition-all cursor-pointer"
        >
          <Maximize2 className="w-3.5 h-3.5 text-[#8e8e93]" />
          <span>Fit Swath</span>
        </button>
      </div>

      {/* Bottom Right: Spatial Telemetry Badge */}
      <div className="absolute bottom-4 right-4 z-20 bg-white/95 backdrop-blur border border-[#e6e6e6] rounded-xl px-3.5 py-2 shadow-tactile text-xs font-sans">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-[#1f1f1f] font-semibold">
            <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
            <span>PostGIS Geodetic Sync</span>
          </div>
          <div className="h-3 w-px bg-slate-200" />
          <span className="text-[11px] font-mono text-[#8e8e93]">
            {contacts.filter(c => c.latitude != null).length} / {contacts.length} Georeferenced
          </span>
        </div>
      </div>
    </div>
  );
};
