import { useEffect } from 'react';
import { MapContainer, TileLayer, Circle, Marker, useMap } from 'react-leaflet';
import L from 'leaflet';
import { MapPin, CloudRain, CloudLightning, Thermometer } from 'lucide-react';
import { renderToString } from 'react-dom/server';

// Fix Leaflet's default icon rendering issues
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const createCustomIcon = (isDanger: boolean) => L.divIcon({
  html: renderToString(
    <div className="relative flex items-center justify-center w-8 h-8">
       <div className={`absolute w-full h-full rounded-full animate-ping opacity-50 ${isDanger ? 'bg-rose-500' : 'bg-primary-500'}`} />
       <div className={`relative z-10 p-1.5 rounded-full shadow-lg border-2 border-white ${isDanger ? 'bg-rose-600' : 'bg-primary-600'}`}>
          <MapPin className="w-4 h-4 text-white" />
       </div>
    </div>
  ),
  className: 'custom-leaflet-icon',
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

interface ZoneMapProps {
  lat: number;
  lng: number;
  radiusKm?: number;
  isDanger?: boolean;
  metrics?: {
    rainProb: number;
    aqi: number;
    temp: number;
  };
}

function MapUpdater({ lat, lng }: { lat: number, lng: number }) {
  const map = useMap();
  useEffect(() => {
    map.flyTo([lat, lng], 10, { duration: 1.5 });
  }, [lat, lng, map]);
  return null;
}

export function ZoneMap({ lat, lng, radiusKm = 15, isDanger = false, metrics }: ZoneMapProps) {
  // Convert km to meters for Leaflet Circle radius
  const radiusMeters = radiusKm * 1000;
  const pinIcon = createCustomIcon(isDanger);

  return (
    <div className={`w-full h-64 rounded-2xl overflow-hidden relative z-0 border shadow-lg transition-colors duration-1000 ${isDanger ? 'border-rose-500/50 shadow-rose-500/20' : 'border-white/10'}`}>
      <MapContainer 
        center={[lat, lng]} 
        zoom={10} 
        style={{ height: '100%', width: '100%', background: '#0f172a' }}
        zoomControl={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
          url="https://{s}.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}{r}.png"
        />
        
        <Circle 
          center={[lat, lng]} 
          radius={radiusMeters} 
          pathOptions={{ 
            color: isDanger ? '#f43f5e' : '#8b5cf6', 
            fillColor: isDanger ? '#f43f5e' : '#8b5cf6', 
            fillOpacity: isDanger ? 0.25 : 0.15,
            weight: 2,
            dashArray: '4 4'
          }} 
        />
        
        <Marker position={[lat, lng]} icon={pinIcon} />
        
        <MapUpdater lat={lat} lng={lng} />
      </MapContainer>
      
      {/* HUD overlay */}
      <div className="absolute top-3 left-3 z-[400] pointer-events-none">
         <div className="bg-black/60 backdrop-blur-md border border-white/10 p-2 rounded-xl text-white shadow-lg">
            <p className="text-[9px] font-black uppercase tracking-widest text-primary-400">Coverage Zone</p>
            <p className="text-sm font-bold">15km Radius</p>
         </div>
      </div>

      {/* Metrics HUD overlay beside map (Right top corner inside map) */}
      {metrics && (
          <div className="absolute top-3 right-3 z-[400] pointer-events-none flex flex-col gap-2">
             <div className="bg-black/60 backdrop-blur-md border border-white/10 px-3 py-2 rounded-xl text-white flex items-center gap-3 shadow-lg">
                 <CloudRain className="w-5 h-5 text-accent-light" />
                 <div className="flex flex-col">
                    <span className="text-[9px] text-gray-400 font-bold uppercase leading-tight tracking-widest">Rain Risk</span>
                    <span className="text-sm font-black leading-tight text-white">{metrics.rainProb}%</span>
                 </div>
             </div>
             <div className="bg-black/60 backdrop-blur-md border border-white/10 px-3 py-2 rounded-xl text-white flex items-center gap-3 shadow-lg">
                 <CloudLightning className="w-5 h-5 text-gray-400" />
                 <div className="flex flex-col">
                    <span className="text-[9px] text-gray-400 font-bold uppercase leading-tight tracking-widest">AQI</span>
                    <span className="text-sm font-black leading-tight text-white">{metrics.aqi}</span>
                 </div>
             </div>
             <div className="bg-black/60 backdrop-blur-md border border-white/10 px-3 py-2 rounded-xl text-white flex items-center gap-3 shadow-lg">
                 <Thermometer className="w-5 h-5 text-amber-500" />
                 <div className="flex flex-col">
                    <span className="text-[9px] text-gray-400 font-bold uppercase leading-tight tracking-widest">Temp</span>
                    <span className="text-sm font-black leading-tight text-white">{metrics.temp}°C</span>
                 </div>
             </div>
          </div>
      )}
    </div>
  );
}
