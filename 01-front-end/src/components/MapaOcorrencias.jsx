import { CircleMarker, MapContainer, Popup, TileLayer } from 'react-leaflet'
import { Link } from 'react-router-dom'
import 'leaflet/dist/leaflet.css'
import { CORES_PRIORIDADE } from './Prioridade'

export default function MapaOcorrencias({ ocorrencias, altura = 380 }) {
  const centro = ocorrencias.length
    ? [ocorrencias[0].lat, ocorrencias[0].lng]
    : [-23.5405, -46.5762]

  return (
    <div className="mapa" style={{ height: altura }} role="region" aria-label="Mapa das ocorrências. A mesma informação está na lista de ocorrências.">
      <MapContainer center={centro} zoom={15} style={{ height: '100%', width: '100%' }} scrollWheelZoom={false}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {ocorrencias.map((o) => (
          <CircleMarker
            key={o.id}
            center={[o.lat, o.lng]}
            radius={o.ia.prioridade === 'Crítica' ? 12 : 9}
            pathOptions={{ color: CORES_PRIORIDADE[o.ia.prioridade], fillOpacity: o.status === 'Concluída' ? 0.15 : 0.6 }}
          >
            <Popup>
              <strong>{o.ia.tipoRotulo}</strong>
              <br />
              {o.endereco}
              <br />
              Prioridade {o.ia.prioridade} · {o.status}
              <br />
              <Link to={`/ocorrencias/${o.id}`}>Ver detalhes</Link>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  )
}
