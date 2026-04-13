import { useEffect, useState, useRef, useCallback } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { translations } from "./translations";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

const TIER_CONFIG = {
  4: { color: "#ef4444", fillOpacity: 0.25 },
  3: { color: "#f97316", fillOpacity: 0.20 },
  2: { color: "#a855f7", fillOpacity: 0.15 },
  1: { color: "#22c55e", fillOpacity: 0.10 },
};

const CATEGORIAS_LIST = [
  "TODOS",
  "DELITO DE BAJO IMPACTO",
  "ROBO A TRANSEUNTE EN VÍA PÚBLICA CON Y SIN VIOLENCIA",
  "ROBO DE VEHÍCULO CON Y SIN VIOLENCIA",
  "HECHO NO DELICTIVO",
  "VIOLACIÓN",
  "ROBO A NEGOCIO CON VIOLENCIA",
  "HOMICIDIO DOLOSO",
];

export default function App() {
  const mapRef = useRef(null);
  const mapDOMRef = useRef(null);
  const layerRef = useRef(null);

  const [lang, setLang] = useState("es");
  const [anio, setAnio] = useState(2024);
  const [aniosDisponibles, setAniosDisponibles] = useState([2026, 2025, 2024]);
  const [categoria, setCategoria] = useState("TODOS");
  const [stats, setStats] = useState([]);
  const [total, setTotal] = useState(0);
  const [cargando, setCargando] = useState(false);
  
  // Drill-down states
  const [selectedAlcaldia, setSelectedAlcaldia] = useState(null);
  const [sidebarVisible, setSidebarVisible] = useState(true);

  const t = translations[lang];

  // Initialize Map
  useEffect(() => {
    if (mapRef.current) return;
    mapRef.current = L.map(mapDOMRef.current, {
      center: [19.32, -99.12],
      zoom: 11,
      zoomControl: false,
    });
    L.control.zoom({ position: "bottomright" }).addTo(mapRef.current);
    L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
      attribution: "© OpenStreetMap © CARTO",
      maxZoom: 18,
    }).addTo(mapRef.current);

    fetch(`${API}/anios`).then(r => r.json()).then(setAniosDisponibles).catch(() => {});
  }, []);

  const drawLayer = useCallback((data, isColoniaView = false) => {
    if (!mapRef.current) return;
    if (layerRef.current) mapRef.current.removeLayer(layerRef.current);

    const geoFile = isColoniaView ? "/colonias.json" : "/alcaldias_high.json";
    
    fetch(geoFile)
      .then(r => r.json())
      .then(geojson => {
        const statsMap = {};
        data.forEach(d => {
          const key = (d.alcaldia || d.colonia).toUpperCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
          statsMap[key] = d;
        });

        layerRef.current = L.geoJSON(geojson, {
          filter: (feature) => {
            if (!isColoniaView) return true;
            const featAlc = feature.properties.alc || feature.properties.alcaldia || "";
            return featAlc.toUpperCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "") === selectedAlcaldia;
          },
          style: (feature) => {
            const nameKey = (isColoniaView ? 
              (feature.properties.colonia || feature.properties.nombre) : 
              (feature.properties.NOMGEO || feature.properties.name)
            ).toUpperCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
            
            const stat = statsMap[nameKey];
            const cfg = TIER_CONFIG[stat?.tier] || { color: "#94a3b8", fillOpacity: 0.05 };
            
            return {
              color: cfg.color,
              weight: isColoniaView ? 1 : 1.5,
              opacity: 0.8,
              fillColor: cfg.color,
              fillOpacity: stat ? cfg.fillOpacity : 0.02,
            };
          },
          onEachFeature: (feature, layer) => {
            const name = isColoniaView ? 
              (feature.properties.colonia || feature.properties.nombre) : 
              (feature.properties.NOMGEO || feature.properties.name);
            
            const nameKey = name.toUpperCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
            const stat = statsMap[nameKey];
            const totalStr = stat ? stat.total.toLocaleString("es-MX") : "—";
            
            // Cifra Negra calculation: 93% not reported = reported is 7%
            const estimatedTotal = stat ? Math.round(stat.total / 0.07) : 0;
            const unreported = estimatedTotal - (stat ? stat.total : 0);

            layer.bindTooltip(`
              <div style="font-family:Inter,sans-serif; min-width:180px">
                <strong style="font-size:14px; color:#1e293b">${name}</strong><br/>
                <div style="margin-top:4px; padding-top:4px; border-top:1px solid #e2e8f0">
                  <span style="color:#64748b; font-size:11px">${t.reported}:</span>
                  <span style="font-weight:700; font-size:13px; float:right">${totalStr}</span>
                </div>
                <div style="margin-top:2px">
                  <span style="color:#ef4444; font-size:11px">${t.estimated_gap}:</span>
                  <span style="font-weight:700; font-size:13px; float:right; color:#ef4444">${unreported.toLocaleString("es-MX")}</span>
                </div>
                <div style="margin-top:4px; padding-top:4px; border-top:1px solid #e2e8f0; font-weight:800; color:#0f172a">
                  <span style="font-size:11px">${t.estimated_total}:</span>
                  <span style="font-size:13px; float:right">${estimatedTotal.toLocaleString("es-MX")}</span>
                </div>
              </div>`, { sticky: true, className: "alcaldia-tooltip" });

            layer.on({
              click: (e) => {
                L.DomEvent.stopPropagation(e);
                if (!isColoniaView) setSelectedAlcaldia(nameKey);
              },
              mouseover: (e) => e.target.setStyle({ fillOpacity: 0.4, weight: 2.5 }),
              mouseout: (e) => layerRef.current.resetStyle(e.target)
            });
          }
        }).addTo(mapRef.current);

        if (isColoniaView && layerRef.current.getBounds().isValid()) {
          mapRef.current.fitBounds(layerRef.current.getBounds(), { padding: [40, 40] });
        } else if (!isColoniaView) {
          mapRef.current.setView([19.32, -99.12], 11);
        }
      });
  }, [selectedAlcaldia, t]);

  useEffect(() => {
    setCargando(true);
    const endpoint = selectedAlcaldia ? 
      `${API}/colonias-stats?alcaldia=${selectedAlcaldia}&anio=${anio}&categoria=${encodeURIComponent(categoria)}` :
      `${API}/alcaldias-stats?anio=${anio}&categoria=${encodeURIComponent(categoria)}`;

    fetch(endpoint)
      .then(r => r.json())
      .then(data => {
        setStats(data);
        setTotal(data.reduce((s, d) => s + d.total, 0));
        drawLayer(data, !!selectedAlcaldia);
        setCargando(false);
      })
      .catch(() => setCargando(false));
  }, [anio, categoria, selectedAlcaldia, drawLayer]);

  const estimatedTotalGlobal = Math.round(total / 0.07);
  const gapGlobal = estimatedTotalGlobal - total;

  return (
    <div className="app-container">
      <button className="mobile-toggle" onClick={() => setSidebarVisible(!sidebarVisible)}>
        {sidebarVisible ? t.menu_close : t.menu_open}
      </button>

      <aside className={`sidebar ${sidebarVisible ? "visible" : ""}`}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 className="title">{t.title}</h1>
            <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>{t.subtitle}</p>
          </div>
          <button 
            onClick={() => setLang(lang === "es" ? "en" : "es")}
            style={{ 
              background: 'var(--bg-color)', border: '1px solid var(--border-color)', 
              borderRadius: '6px', padding: '4px 8px', cursor: 'pointer', fontSize: '10px', fontWeight: 700 
            }}
          >
            {t.lang_switch}
          </button>
        </div>

        {selectedAlcaldia && (
          <button className="select-control" style={{ marginBottom: '10px', backgroundColor: 'var(--primary)', color: 'white' }} onClick={() => setSelectedAlcaldia(null)}>
            {t.back_to_alcaldias}
          </button>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
          <div>
            <label className="label">{t.year}</label>
            <select className="select-control" value={anio} onChange={(e) => setAnio(+e.target.value)}>
              {aniosDisponibles.map(a => <option key={a} value={a}>{a}</option>)}
            </select>
          </div>
          <div>
            <label className="label">{t.crime}</label>
            <select className="select-control" style={{ paddingRight: '20px', textOverflow: 'ellipsis' }} value={categoria} onChange={(e) => setCategoria(e.target.value)}>
              {CATEGORIAS_LIST.map(c => (
                <option key={c} value={c}>{t.categories[c] || c}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="stat-card" style={{ background: '#f8fafc' }}>
          <div className="stat-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
             <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                {t.total_count}
                <span className="info-icon" data-tooltip={t.tooltip_reported}>?</span>
             </span>
             <span style={{ color: '#10b981' }}>7%</span>
          </div>
          <div className={`stat-value ${cargando ? "loading" : ""}`}>
            {cargando ? "…" : total.toLocaleString("es-MX")}
          </div>
        </div>

        <div className="stat-card" style={{ border: '1px solid #ef4444', backgroundColor: '#fef2f2' }}>
          <div className="stat-label" style={{ color: '#ef4444', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                {t.estimated_gap}
                <span className="info-icon" style={{ borderColor: '#ef4444', color: '#ef4444' }} data-tooltip={t.tooltip_gap}>?</span>
            </span>
            <span>93%</span>
          </div>
          <div className="stat-value" style={{ color: '#ef4444' }}>
            {cargando ? "…" : gapGlobal.toLocaleString("es-MX")}
          </div>
        </div>

        <div className="stat-card" style={{ background: 'var(--text-primary)', color: 'white' }}>
          <div className="stat-label" style={{ color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '4px' }}>
            {t.estimated_total}
            <span className="info-icon" style={{ borderColor: '#94a3b8', color: '#94a3b8' }} data-tooltip={t.tooltip_total}>?</span>
          </div>
          <div className="stat-value" style={{ color: 'white' }}>
            {cargando ? "…" : estimatedTotalGlobal.toLocaleString("es-MX")}
          </div>
        </div>

        <div className="legend-container">
          <label className="label" style={{ marginBottom: 12 }}>
            {selectedAlcaldia ? `${t.view_details} ${selectedAlcaldia.charAt(0).toUpperCase() + selectedAlcaldia.slice(1).toLowerCase()}` : t.levels}
          </label>
          {[4, 3, 2, 1].map(tier => (
            <div key={tier} style={{ marginBottom: 14 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <span style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: TIER_CONFIG[tier].color }} />
                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: TIER_CONFIG[tier].color }}>{t[`tier_${tier}`]}</span>
              </div>
              <div style={{ paddingLeft: 4 }}>
                {stats.filter(s => s.tier === tier).map(s => {
                  const estLocal = Math.round(s.total / 0.07);
                  return (
                    <div key={s.alcaldia || s.colonia} style={{ 
                      padding: '8px 0', borderBottom: '1px solid var(--border-color)',
                      display: 'flex', flexDirection: 'column', gap: '2px'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{s.alcaldia || s.colonia}</span>
                        <span style={{ fontWeight: 700 }}>{s.total.toLocaleString("es-MX")}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem', color: '#ef4444', opacity: 0.8 }}>
                        <span>{t.estimated_total} (INEGI)</span>
                        <span>{estLocal.toLocaleString("es-MX")}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        <div className="footer-info">
          {t.footer_data} <strong>FGJ CDMX</strong> · {t.footer_license}<br/>
          <span style={{ fontSize: '0.6rem', opacity: 0.8 }}>{t.inegi_note}</span>
        </div>
      </aside>

      <main ref={mapDOMRef} className="map-container" />
    </div>
  );
}
