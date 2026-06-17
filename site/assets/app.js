const DATA_STATIONS_URL = './data/stations_geo.csv';
// NOTE: stations_geo.csv must exist (generated from AQI.csv) for the app to work.


const citySelect = document.getElementById('citySelect');
const pollutantSelect = document.getElementById('pollutantSelect');
const viewMode = document.getElementById('viewMode');
const resetBtn = document.getElementById('resetBtn');
const statusBox = document.getElementById('statusBox');
const mapMeta = document.getElementById('metaText');
const chartMeta = document.getElementById('chartMeta');

let allRows = [];
let leafletMap;
let markerLayer;
let markersIndex = [];

function safeNum(v){
  if (v === null || v === undefined) return null;
  if (typeof v === 'number') return Number.isFinite(v) ? v : null;
  const s = String(v).trim();
  if (!s || s.toLowerCase() === 'na' || s.toLowerCase() === 'nan') return null;
  if (s === 'NA' || s === 'NaN') return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
}

function parseCSV(text){
  // Simple CSV parser supporting quoted commas; good enough for this dataset.
  // Returns array of objects keyed by header.
  const rows = [];
  const lines = [];
  let cur = '';
  let inQuotes = false;
  for (let i=0;i<text.length;i++){
    const ch = text[i];
    const next = text[i+1];
    if (ch === '"'){
      if (inQuotes && next === '"'){
        cur += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }
    if (ch === '\n' && !inQuotes){
      lines.push(cur);
      cur='';
      continue;
    }
    if (ch === '\r') continue;
    cur += ch;
  }
  if (cur.trim().length) lines.push(cur);

  if (!lines.length) return rows;
  const header = splitCSVLine(lines[0]);
  for (let li=1; li<lines.length; li++){
    if (!lines[li].trim()) continue;
    const cols = splitCSVLine(lines[li]);
    const obj = {};
    for (let ci=0; ci<header.length; ci++){
      obj[header[ci]] = cols[ci] ?? '';
    }
    rows.push(obj);
  }
  return rows;
}

function splitCSVLine(line){
  const out = [];
  let cur='';
  let inQuotes=false;
  for (let i=0;i<line.length;i++){
    const ch=line[i];
    const next=line[i+1];
    if (ch==='"'){
      if (inQuotes && next==='"'){
        cur+='"';
        i++;
      } else {
        inQuotes=!inQuotes;
      }
      continue;
    }
    if (ch===',' && !inQuotes){
      out.push(cur);
      cur='';
      continue;
    }
    cur+=ch;
  }
  out.push(cur);
  return out;
}

function initMap(){
  leafletMap = L.map('map', { zoomControl: true });
  // Rough center over India
  leafletMap.setView([22.9734, 78.6569], 4);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(leafletMap);

  markerLayer = L.layerGroup().addTo(leafletMap);
}

function setSelectOptions(selectEl, values){
  selectEl.innerHTML = '';
  for (const v of values){
    const opt = document.createElement('option');
    opt.value = v;
    opt.textContent = v;
    selectEl.appendChild(opt);
  }
}

function uniqueSorted(arr){
  return Array.from(new Set(arr)).filter(Boolean).sort((a,b)=>String(a).localeCompare(String(b)));
}

function getSelection(){
  return {
    city: citySelect.value,
    pollutant_id: pollutantSelect.value,
    mode: viewMode.value
  };
}

function clearMarkers(){
  if (!markerLayer) return;
  markerLayer.clearLayers();
  markersIndex = [];
}

function renderMap(filtered){
  clearMarkers();

  const latLngs = [];
  for (const r of filtered){
    const lat = safeNum(r.latitude);
    const lon = safeNum(r.longitude);
    if (lat === null || lon === null) continue;
    latLngs.push([lat, lon]);

    const avg = safeNum(r.pollutant_avg);
    const minv = safeNum(r.pollutant_min);
    const maxv = safeNum(r.pollutant_max);

    const label = r.station || '(unknown station)';
    const pollutant = r.pollutant_id;

    const html = `
      <div style="min-width:220px;">
        <div style="font-weight:700; margin-bottom:6px;">${escapeHtml(label)}</div>
        <div style="color:#555; font-size:12px; margin-bottom:2px;">Pollutant: <b>${escapeHtml(pollutant)}</b></div>
        <div style="color:#555; font-size:12px;">Avg: <b>${avg===null ? 'NA' : avg}</b></div>
        <div style="color:#555; font-size:12px;">Min/Max: <b>${minv===null?'NA':minv} / ${maxv===null?'NA':maxv}</b></div>
      </div>
    `;

    const m = L.marker([lat, lon]).bindPopup(html);
    markerLayer.addLayer(m);
  }

  if (latLngs.length){
    const bounds = L.latLngBounds(latLngs);
    leafletMap.fitBounds(bounds.pad(0.2));
  }
}

function escapeHtml(str){
  return String(str)
    .replaceAll('&','&amp;')
    .replaceAll('<','<')
    .replaceAll('>','>')
    .replaceAll('"','"')
    .replaceAll("'",'&#039;');
}

function renderChart(filtered){
  const mode = viewMode.value;
  const x = filtered.map(r => r.station || '(unknown station)');
  const yAvg = filtered.map(r => safeNum(r.pollutant_avg));
  const yMin = filtered.map(r => safeNum(r.pollutant_min));
  const yMax = filtered.map(r => safeNum(r.pollutant_max));

  const validIdx = filtered.map((_,i)=>i).filter(i=>{
    if (mode === 'avg') return yAvg[i] !== null;
    return yMin[i] !== null || yMax[i] !== null;
  });

  const x2 = validIdx.map(i=>x[i]);
  const avg2 = validIdx.map(i=>yAvg[i]);
  const min2 = validIdx.map(i=>yMin[i]);
  const max2 = validIdx.map(i=>yMax[i]);

  const pollutant = filtered[0]?.pollutant_id || '';
  const city = filtered[0]?.city || '';

  chartMeta.textContent = `${city} • ${pollutant} • stations: ${x2.length}`;

  if (mode === 'avg'){
    const trace = {
      type: 'bar',
      x: x2,
      y: avg2,
      marker: { color: 'rgba(78,161,255,.9)' },
      name: 'Pollutant Avg'
    };

    const layout = {
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      margin: { l: 60, r: 20, t: 30, b: 90 },
      xaxis: { tickangle: -45, automargin: true },
      yaxis: { title: 'Pollutant Avg' },
      font: { color: '#e8eefc' },
      showlegend: false,
      title: { text: 'Pollutant Avg by Station', font: { size: 14 } }
    };

    Plotly.newPlot('chart', [trace], layout, { responsive: true });
    return;
  }

  // min/max
  const traceMin = {
    type: 'scatter',
    mode: 'lines+markers',
    x: x2,
    y: min2,
    name: 'Min',
    line: { color: 'rgba(124,92,255,.95)' },
    marker: { size: 6, color: 'rgba(124,92,255,.95)' }
  };

  const traceMax = {
    type: 'scatter',
    mode: 'lines+markers',
    x: x2,
    y: max2,
    name: 'Max',
    line: { color: 'rgba(78,161,255,.95)' },
    marker: { size: 6, color: 'rgba(78,161,255,.95)' }
  };

  const layout = {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    margin: { l: 60, r: 20, t: 30, b: 90 },
    xaxis: { tickangle: -45, automargin: true },
    yaxis: { title: 'Pollutant value' },
    font: { color: '#e8eefc' },
    legend: { orientation: 'h' },
    title: { text: 'Pollutant Min/Max by Station', font: { size: 14 } }
  };

  Plotly.newPlot('chart', [traceMin, traceMax], layout, { responsive: true });
}

function update(){
  const { city, pollutant_id } = getSelection();
  const filtered = allRows.filter(r => r.city === city && r.pollutant_id === pollutant_id);

  mapMeta.textContent = `${city} • ${pollutant_id} • ${filtered.length} records`;
  chartMeta.textContent = '—';

  renderMap(filtered);
  renderChart(filtered);
}

async function load(){
  try{
    statusBox.textContent = 'Loading station data...';
    const res = await fetch(DATA_STATIONS_URL);
    if (!res.ok) throw new Error(`Failed to fetch ${DATA_STATIONS_URL}: ${res.status}`);
    const text = await res.text();
    const rows = parseCSV(text);

    // normalize numeric fields
    allRows = rows.map(r => ({
      country: r.country,
      state: r.state,
      city: r.city,
      station: r.station,
      last_update: r.last_update,
      latitude: r.latitude,
      longitude: r.longitude,
      pollutant_id: r.pollutant_id,
      pollutant_min: r.pollutant_min,
      pollutant_max: r.pollutant_max,
      pollutant_avg: r.pollutant_avg,
    }));

    const cities = uniqueSorted(allRows.map(r => r.city));
    const pollutants = uniqueSorted(allRows.map(r => r.pollutant_id));

    setSelectOptions(citySelect, cities);
    setSelectOptions(pollutantSelect, pollutants);

    citySelect.disabled = false;
    pollutantSelect.disabled = false;

    // default selections
    citySelect.value = cities[0] || '';
    pollutantSelect.value = pollutants[0] || '';

    initMap();
    statusBox.textContent = 'Ready';
    update();

    citySelect.addEventListener('change', update);
    pollutantSelect.addEventListener('change', update);
    viewMode.addEventListener('change', update);
    resetBtn.addEventListener('click', () => {
      citySelect.value = cities[0] || '';
      pollutantSelect.value = pollutants[0] || '';
      viewMode.value = 'avg';
      update();
    });
  } catch (e){
    console.error(e);
    statusBox.textContent = 'Failed to load data. Ensure site/data/stations_geo.csv exists.';
  }
}

load();

