import React, { useEffect } from 'react';
import maplibregl from 'maplibre-gl';
import { DriftForecastDetail } from '../../types/drift';

interface DriftLayerProps {
  map: maplibregl.Map | null;
  forecast: DriftForecastDetail | null;
  visible?: boolean;
  showUncertainty?: boolean;
}

export const DriftLayer: React.FC<DriftLayerProps> = ({
  map,
  forecast,
  visible = true,
  showUncertainty = true,
}) => {
  useEffect(() => {
    if (!map) return;

    const sourceId = 'drift-forecast-source';
    const lineLayerId = 'drift-trajectory-line';
    const pointsLayerId = 'drift-milestone-points';
    const labelsLayerId = 'drift-milestone-labels';
    const polyLayerId = 'drift-uncertainty-polygon';
    const polyOutlineId = 'drift-uncertainty-outline';

    const cleanupLayers = () => {
      if (map.getLayer(labelsLayerId)) map.removeLayer(labelsLayerId);
      if (map.getLayer(pointsLayerId)) map.removeLayer(pointsLayerId);
      if (map.getLayer(lineLayerId)) map.removeLayer(lineLayerId);
      if (map.getLayer(polyOutlineId)) map.removeLayer(polyOutlineId);
      if (map.getLayer(polyLayerId)) map.removeLayer(polyLayerId);
      if (map.getSource(sourceId)) map.removeSource(sourceId);
    };

    if (!forecast || !visible || !forecast.geojson) {
      cleanupLayers();
      return;
    }

    cleanupLayers();

    try {
      map.addSource(sourceId, {
        type: 'geojson',
        data: forecast.geojson,
      });

      // 1. Uncertainty Polygons (translucent buffer fill)
      if (showUncertainty) {
        map.addLayer({
          id: polyLayerId,
          type: 'fill',
          source: sourceId,
          filter: ['==', '$type', 'Polygon'],
          paint: {
            'fill-color': '#f59e0b',
            'fill-opacity': 0.15,
          },
        });

        map.addLayer({
          id: polyOutlineId,
          type: 'line',
          source: sourceId,
          filter: ['==', '$type', 'Polygon'],
          paint: {
            'line-color': '#f59e0b',
            'line-width': 1.5,
            'line-dasharray': [3, 2],
            'line-opacity': 0.6,
          },
        });
      }

      // 2. Trajectory Line
      map.addLayer({
        id: lineLayerId,
        type: 'line',
        source: sourceId,
        filter: ['==', '$type', 'LineString'],
        paint: {
          'line-color': '#00d2ff',
          'line-width': 3.5,
          'line-opacity': 0.9,
        },
      });

      // 3. Milestone Points (24h, 48h, 72h)
      map.addLayer({
        id: pointsLayerId,
        type: 'circle',
        source: sourceId,
        filter: ['==', '$type', 'Point'],
        paint: {
          'circle-radius': 6,
          'circle-color': '#f59e0b',
          'circle-stroke-width': 2.5,
          'circle-stroke-color': '#ffffff',
        },
      });

      // Popup on point click
      const onPointClick = (e: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }) => {
        if (!e.features || e.features.length === 0) return;
        const feat = e.features[0];
        const props = feat.properties || {};

        new maplibregl.Popup({ offset: 10 })
          .setLngLat(e.lngLat)
          .setHTML(`
            <div style="font-family: sans-serif; font-size: 11px; padding: 4px; color: #1e293b;">
              <div style="font-weight: bold; color: #d97706; margin-bottom: 2px;">
                FORECAST HORIZON: ${props.milestone || 'Waypoint'}
              </div>
              <div><b>Model:</b> ${props.model_name || forecast.model_name}</div>
              <div><b>Distance:</b> ${props.distance_km || '—'} km</div>
              <div><b>Speed:</b> ${props.speed_ms || '—'} m/s</div>
              <div><b>Heading:</b> ${props.heading_deg || '—'}°</div>
              <div><b>Uncertainty:</b> ±${props.uncertainty_radius_km || '—'} km</div>
            </div>
          `)
          .addTo(map);
      };

      map.on('click', pointsLayerId, onPointClick);

      // Fit map to trajectory bounding box
      const coords = forecast.geojson.features
        .filter((f: any) => f.geometry.type === 'LineString')
        .flatMap((f: any) => f.geometry.coordinates);

      if (coords.length > 0) {
        const bounds = coords.reduce(
          (b: maplibregl.LngLatBounds, c: [number, number]) => b.extend(c),
          new maplibregl.LngLatBounds(coords[0], coords[0])
        );
        map.fitBounds(bounds, { padding: 80, maxZoom: 14 });
      }

      return () => {
        map.off('click', pointsLayerId, onPointClick);
        cleanupLayers();
      };
    } catch (err) {
      console.warn('DriftLayer error adding layers:', err);
    }
  }, [map, forecast, visible, showUncertainty]);

  return null;
};
