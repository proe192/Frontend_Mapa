from flask import Flask, jsonify, request
import numpy as np
import mysql.connector

app = Flask(__name__)

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'quetzaltenango_grafo'
}

# Variables globales para almacenar los datos
LUGARES = []
MATRIZ_ADY = None
MATRIZ_DIST = None

def cargar_datos():
    """Carga los datos desde la base de datos"""
    global LUGARES, MATRIZ_ADY, MATRIZ_DIST
    
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    # Obtener lugares únicos
    cursor.execute("SELECT DISTINCT origen FROM distancias_adyacencia ORDER BY origen")
    LUGARES = [row['origen'] for row in cursor.fetchall()]
    n = len(LUGARES)
    
    # Inicializar matrices
    MATRIZ_ADY = np.zeros((n, n), dtype=int)
    MATRIZ_DIST = np.zeros((n, n), dtype=float)
    
    # Llenar matrices
    cursor.execute("SELECT origen, destino, distancia_km, adyacente FROM distancias_adyacencia")
    for row in cursor.fetchall():
        i = LUGARES.index(row['origen'])
        j = LUGARES.index(row['destino'])
        MATRIZ_ADY[i][j] = row['adyacente']
        MATRIZ_DIST[i][j] = row['distancia_km']
    
    cursor.close()
    conn.close()

def warshall(matriz):
    """Algoritmo de Warshall para matriz de conectividad"""
    n = len(matriz)
    matriz_c = np.copy(matriz)
    
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if matriz_c[i][k] and matriz_c[k][j]:
                    matriz_c[i][j] = 1
    return matriz_c

def dijkstra(origen_idx, destino_idx):
    """Algoritmo de Dijkstra para camino mínimo"""
    n = len(MATRIZ_ADY)
    dist = [float('inf')] * n
    prev = [-1] * n
    dist[origen_idx] = 0
    no_visitados = set(range(n))
    
    while no_visitados:
        u = min(no_visitados, key=lambda x: dist[x])
        no_visitados.remove(u)
        
        for v in range(n):
            if MATRIZ_ADY[u][v] and MATRIZ_DIST[u][v] > 0:
                nueva_dist = dist[u] + MATRIZ_DIST[u][v]
                if nueva_dist < dist[v]:
                    dist[v] = nueva_dist
                    prev[v] = u
    
    # Reconstruir camino
    camino = []
    u = destino_idx
    if prev[u] != -1 or u == origen_idx:
        while u != -1:
            camino.insert(0, LUGARES[u])
            u = prev[u]
    
    return {
        "distancia": dist[destino_idx],
        "camino": camino if camino else None
    }

# --------------------------------------------------
# ENDPOINTS (comienzan aquí)
# --------------------------------------------------

@app.route('/')
def home():
    """Endpoint raíz para verificar que la API está funcionando"""
    return "API de Rutas Quetzaltenango - USAC está en funcionamiento"

@app.route('/api/lugares', methods=['GET'])
def get_lugares():
    """Devuelve la lista de todos los lugares disponibles"""
    return jsonify({
        "success": True,
        "count": len(LUGARES),
        "lugares": LUGARES
    })

@app.route('/api/conectividad', methods=['GET'])
def verificar_conectividad():
    """
    Verifica si existe un camino entre dos lugares
    Parámetros: origen, destino
    Ejemplo: /api/conectividad?origen=USAC&destino=ParqueCentral
    """
    origen = request.args.get('origen')
    destino = request.args.get('destino')
    
    if not origen or not destino:
        return jsonify({
            "success": False,
            "error": "Se requieren los parámetros 'origen' y 'destino'"
        }), 400
    
    try:
        i = LUGARES.index(origen)
        j = LUGARES.index(destino)
        matriz_conectividad = warshall(MATRIZ_ADY)
        
        return jsonify({
            "success": True,
            "conectado": bool(matriz_conectividad[i][j]),
            "origen": origen,
            "destino": destino,
            "conexion_directa": bool(MATRIZ_ADY[i][j])  # Si es conexión directa
        })
        
    except ValueError:
        return jsonify({
            "success": False,
            "error": "Lugar no encontrado en la base de datos"
        }), 404

@app.route('/api/camino-minimo', methods=['GET'])
def encontrar_camino_minimo():
    """
    Calcula la ruta más corta entre dos lugares
    Parámetros: origen, destino
    Ejemplo: /api/camino-minimo?origen=USAC&destino=ParqueCentral
    """
    origen = request.args.get('origen')
    destino = request.args.get('destino')
    
    if not origen or not destino:
        return jsonify({
            "success": False,
            "error": "Se requieren los parámetros 'origen' y 'destino'"
        }), 400
    
    try:
        i = LUGARES.index(origen)
        j = LUGARES.index(destino)
        resultado = dijkstra(i, j)
        
        if not resultado["camino"]:
            return jsonify({
                "success": False,
                "error": f"No existe camino entre {origen} y {destino}"
            }), 404
        
        return jsonify({
            "success": True,
            "origen": origen,
            "destino": destino,
            "distancia": resultado["distancia"],
            "camino": resultado["camino"]
        })
        
    except ValueError:
        return jsonify({
            "success": False,
            "error": "Lugar no encontrado en la base de datos"
        }), 404

@app.route('/api/matrices', methods=['GET'])
def get_matrices():
    """
    Devuelve las matrices completas (para debugging)
    """
    return jsonify({
        "success": True,
        "lugares": LUGARES,
        "matriz_adyacencia": MATRIZ_ADY.tolist(),
        "matriz_distancias": MATRIZ_DIST.tolist(),
        "matriz_conectividad": warshall(MATRIZ_ADY).tolist()
    })

# --------------------------------------------------
# Inicialización y ejecución
# --------------------------------------------------

# Cargar datos al iniciar
cargar_datos()

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')