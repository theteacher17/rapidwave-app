import os
from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

# --- CONFIGURACIÓN ---
API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "TU_API_KEY_AQUI")
NUMERO_WHATSAPP = "13478978768"
NUMERO_SMS = "15551234567"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>RapidWave Logistics Pro</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root { --primary: #2563eb; --dark: #0f172a; --light: #f8fafc; }
        body { font-family: 'Plus Jakarta Sans', sans-serif; margin: 0; background: var(--light); color: var(--dark); overflow: hidden; }
        #map { height: 100vh; width: 100%; position: absolute; z-index: 1; }
        
        .side-panel {
            position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
            width: 92%; max-width: 450px; background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(12px); border-radius: 24px; padding: 24px; z-index: 10;
            box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); box-sizing: border-box;
        }

        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .logo { font-weight: 800; font-size: 22px; letter-spacing: -1px; }
        .lang-btn { background: var(--dark); color: white; border: none; padding: 6px 12px; border-radius: 99px; font-size: 12px; font-weight: 600; cursor: pointer; }

        .input-group { position: relative; margin-bottom: 10px; }
        .input-group input {
            width: 100%; padding: 14px; border-radius: 12px; border: 1px solid #e2e8f0;
            background: white; font-size: 15px; box-sizing: border-box; outline: none;
        }

        .btn-main {
            width: 100%; padding: 16px; border-radius: 14px; background: var(--primary);
            color: white; border: none; font-size: 16px; font-weight: 700; cursor: pointer; margin-top: 10px;
        }

        .btn-add { background: none; color: var(--primary); border: none; font-weight: 600; font-size: 14px; margin-bottom: 15px; cursor: pointer; padding: 0; }

        #result { display: none; margin-top: 20px; padding-top: 20px; border-top: 1px solid #f1f5f9; }
        .price-container { text-align: center; margin-bottom: 15px; }
        .price-val { font-size: 42px; font-weight: 800; }
        
        .details-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .detail-card { background: #f1f5f9; padding: 12px; border-radius: 12px; text-align: center; }
        .detail-card span { display: block; font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 700; }
        .detail-card b { font-size: 16px; }

        .action-btns { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 20px; }
        .action-btn { text-decoration: none; text-align: center; padding: 14px; border-radius: 12px; color: white; font-weight: 700; font-size: 14px; }
        .wa { background: #22c55e; } .sm { background: var(--dark); }
    </style>
</head>
<body>

<div id="map"></div>

<div class="side-panel">
    <header>
        <div class="logo">RapidWave<span style="color:var(--primary)">.</span></div>
        <button class="lang-btn" id="lang-switch" onclick="toggleLanguage()">EN</button>
    </header>

    <div id="stops-container">
        <div class="input-group"><input type="text" class="stop-input" id="p1" placeholder="Punto de Recogida"></div>
        <div class="input-group"><input type="text" class="stop-input" id="p2" placeholder="Destino Final"></div>
    </div>

    <button class="btn-add" id="btn-add-text" onclick="addInput()">+ Agregar parada</button>
    <button class="btn-main" id="calc-btn" onclick="calculate()">Calcular Cotización</button>

    <div id="result">
        <div class="price-container">
            <span style="font-size:14px; color:#64748b; font-weight:600;" id="txt-res-label">Inversión Estimada</span>
            <div class="price-val" id="res-price">$0.00</div>
        </div>
        <div class="details-grid">
            <div class="detail-card"><span id="txt-dist-label">Distancia</span><b id="res-dist">0 mi</b></div>
            <div class="detail-card"><span id="txt-time-label">Tiempo</span><b id="res-time">0 min</b></div>
        </div>
        <div class="action-btns">
            <a id="whatsapp" class="action-btn wa" href="#" target="_blank">WhatsApp</a>
            <a id="sms" class="action-btn sm" href="#" target="_blank">SMS</a>
        </div>
    </div>
</div>

<script src="https://maps.googleapis.com/maps/api/js?key={{ api_key }}&libraries=places"></script>
<script>
    let currentLang = 'es';
    const translations = {
        es: { 
            add: "+ Agregar parada", 
            calc: "Calcular Cotización", 
            wait: "Analizando...", 
            extra: "Parada Extra", 
            p1: "Punto de Recogida",
            p2: "Destino Final",
            res_label: "Inversión Estimada",
            dist_label: "Distancia",
            time_label: "Tiempo",
            wa_header: "*NUEVA SOLICITUD RAPIDWAVE*\\n\\n",
            wa_origin: "Origen",
            wa_dest: "Destino",
            wa_stop: "Parada",
            wa_stats: "DETALLES",
            wa_dist: "Distancia",
            wa_time: "Tiempo (Tráfico)",
            wa_tolls: "Peajes Incluidos",
            wa_total: "TOTAL ESTIMADO"
        },
        en: { 
            add: "+ Add stop", 
            calc: "Calculate Quote", 
            wait: "Analyzing...", 
            extra: "Extra stop", 
            p1: "Pickup Location",
            p2: "Final Destination",
            res_label: "Estimated Investment",
            dist_label: "Distance",
            time_label: "Time",
            wa_header: "*NEW RAPIDWAVE REQUEST*\\n\\n",
            wa_origin: "Origin",
            wa_dest: "Destination",
            wa_stop: "Stop",
            wa_stats: "DETAILS",
            wa_dist: "Distance",
            wa_time: "Time (Traffic)",
            wa_tolls: "Tolls Included",
            wa_total: "ESTIMATED TOTAL"
        }
    };

    let map, directionsService, directionsRenderer;

    function initMap() {
        map = new google.maps.Map(document.getElementById('map'), {
            center: {lat: 40.7128, lng: -74.0060}, zoom: 12, disableDefaultUI: true,
            styles: [{ "featureType": "all", "elementType": "geometry", "stylers": [{ "color": "#f5f5f5" }] }]
        });
        directionsService = new google.maps.DirectionsService();
        directionsRenderer = new google.maps.DirectionsRenderer({ map: map });
        setupAutocomplete();
    }

    function setupAutocomplete() {
        document.querySelectorAll('.stop-input').forEach(input => new google.maps.places.Autocomplete(input));
    }

    function toggleLanguage() {
        currentLang = currentLang === 'es' ? 'en' : 'es';
        const t = translations[currentLang];
        
        // Traducir Interfaz
        document.getElementById('lang-switch').innerText = currentLang === 'es' ? 'EN' : 'ES';
        document.getElementById('btn-add-text').innerText = t.add;
        document.getElementById('calc-btn').innerText = t.calc;
        document.getElementById('txt-res-label').innerText = t.res_label;
        document.getElementById('txt-dist-label').innerText = t.dist_label;
        document.getElementById('txt-time-label').innerText = t.time_label;
        
        // Traducir Placeholders
        document.getElementById('p1').placeholder = t.p1;
        document.getElementById('p2').placeholder = t.p2;
        document.querySelectorAll('.stop-input').forEach((input, i) => {
            if(i > 1) input.placeholder = t.extra;
        });
    }

    function addInput() {
        const div = document.createElement('div');
        div.className = 'input-group';
        div.innerHTML = `<input type="text" class="stop-input" placeholder="${translations[currentLang].extra}">`;
        document.getElementById('stops-container').appendChild(div);
        setupAutocomplete();
    }

    async function calculate() {
        const btn = document.getElementById('calc-btn');
        const inputs = document.querySelectorAll('.stop-input');
        const stops = Array.from(inputs).map(i => i.value.trim()).filter(i => i);

        if(stops.length < 2) return;
        btn.disabled = true; 
        const originalBtnText = btn.innerText;
        btn.innerText = translations[currentLang].wait;

        try {
            const res = await fetch(`/calcular?stops=${encodeURIComponent(stops.join('|'))}`);
            const data = await res.json();
            const t = translations[currentLang];

            document.getElementById('result').style.display = 'block';
            document.getElementById('res-price').innerText = `$${data.precio}`;
            document.getElementById('res-dist').innerText = `${data.millas} mi`;
            document.getElementById('res-time').innerText = `${data.minutos} min`;

            // CONSTRUCCIÓN DEL MENSAJE DETALLADO BILINGÜE
            let routeText = "";
            stops.forEach((s, idx) => { 
                let label = idx === 0 ? t.wa_origin : (idx === stops.length-1 ? t.wa_dest : t.wa_stop);
                routeText += `📍 *${label}*: ${s}\\n`; 
            });

            const fullMsg = `${t.wa_header}` +
                            `${routeText}\\n` +
                            `📊 *${t.wa_stats}:*\\n` +
                            `- ${t.wa_dist}: ${data.millas} mi\\n` +
                            `- ${t.wa_time}: ${data.minutos} min\\n` +
                            `- ${t.wa_tolls}: $${data.tolls}\\n\\n` +
                            `💰 *${t.wa_total}: $${data.precio}*`;

            document.getElementById('whatsapp').href = `https://wa.me/{{ numero_whatsapp }}?text=${encodeURIComponent(fullMsg)}`;
            document.getElementById('sms').href = `sms:{{ numero_sms }}?body=${encodeURIComponent(fullMsg)}`;

            directionsService.route({
                origin: stops[0], destination: stops[stops.length-1],
                waypoints: stops.slice(1, -1).map(s => ({ location: s, stopover: true })),
                travelMode: 'DRIVING', drivingOptions: { departureTime: new Date(), trafficModel: 'pessimistic' }
            }, (res, status) => { if(status === 'OK') directionsRenderer.setDirections(res); });

        } catch (e) { alert("Error"); }
        finally { btn.disabled = false; btn.innerText = translations[currentLang].calc; }
    }
    window.onload = initMap;
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, api_key=API_KEY, numero_whatsapp=NUMERO_WHATSAPP, numero_sms=NUMERO_SMS)

@app.route('/calcular')
def calcular():
    stops_param = request.args.get('stops')
    stops = stops_param.split('|')
    total_distance = 0
    total_duration_traffic = 0
    total_tolls = 0

    BASE_FARE = 5.00
    MIN_FARE = 35.00
    PER_MINUTE = 0.40
    PER_MILE = 1.80

    for i in range(len(stops)-1):
        params = {"origin": stops[i], "destination": stops[i+1], "key": API_KEY, "departure_time": "now", "traffic_model": "pessimistic"}
        r = requests.get("https://maps.googleapis.com/maps/api/directions/json", params=params).json()
        
        if r.get('status') == 'OK':
            route = r['routes'][0]
            leg = route['legs'][0]
            total_distance += leg['distance']['value']
            total_duration_traffic += leg.get('duration_in_traffic', leg['duration'])['value']
            
            warnings = " ".join(route.get('warnings', [])).lower()
            addr = (stops[i] + " " + stops[i+1]).upper()
            if 'toll' in warnings:
                if ' NY ' in addr and ' NJ ' in addr: total_tolls += 17.50
                elif ' MD ' in addr: total_tolls += 9.50
                else: total_tolls += 7.00

    millas = round(total_distance / 1609.34, 2)
    minutos = round(total_duration_traffic / 60, 1)

    subtotal = BASE_FARE + (minutos * PER_MINUTE) + (millas * PER_MILE) + total_tolls
    precio_final = round(max(subtotal, MIN_FARE), 2)

    return jsonify({
        "precio": precio_final,
        "millas": millas,
        "minutos": minutos,
        "tolls": round(total_tolls, 2)
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
