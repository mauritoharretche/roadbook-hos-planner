import { useEffect } from "react";
import { CircleMarker, MapContainer, Polyline, TileLayer, Tooltip, useMap } from "react-leaflet";
import type { LatLngBoundsExpression } from "leaflet";

import type { Route } from "../../types/trip";

interface RouteMapProps {
  route: Route;
}

const waypointColors = {
  current: "#215b8d",
  pickup: "#cc7a00",
  dropoff: "#147d64",
};

export function RouteMap({ route }: RouteMapProps) {
  const positions = route.geometry.map(([longitude, latitude]) => [latitude, longitude] as [number, number]);
  const center = positions[0] ?? [-34.6037, -58.3816];

  return (
    <section aria-label="Trip route map" className="map-card panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Route overview</p>
          <h2>Planned route</h2>
        </div>
        <span className="map-caption">Route geometry</span>
      </div>
      <MapContainer center={center} className="route-map" scrollWheelZoom={false} zoom={7}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Polyline color="#215b8d" pathOptions={{ weight: 5 }} positions={positions} />
        {route.waypoints.map((waypoint) => (
          <CircleMarker
            center={[waypoint.latitude, waypoint.longitude]}
            color={waypointColors[waypoint.kind]}
            fillColor={waypointColors[waypoint.kind]}
            fillOpacity={1}
            key={waypoint.kind}
            radius={9}
            weight={3}
          >
            <Tooltip direction="top" offset={[0, -10]}>
              <strong>{waypoint.kind}</strong>
              <br />
              {waypoint.label}
            </Tooltip>
          </CircleMarker>
        ))}
        <FitRoute positions={positions} />
      </MapContainer>
      <div className="map-legend" aria-label="Route marker legend">
        <span><i className="legend-dot current" />Current</span>
        <span><i className="legend-dot pickup" />Pickup</span>
        <span><i className="legend-dot dropoff" />Dropoff</span>
      </div>
    </section>
  );
}

function FitRoute({ positions }: { positions: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (positions.length > 1) {
      map.fitBounds(positions as LatLngBoundsExpression, { padding: [32, 32] });
    }
  }, [map, positions]);
  return null;
}
