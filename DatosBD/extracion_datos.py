import requests
import json
from tabulate import tabulate  # Instalar con: pip install tabulate

def test_api():
    """Función para probar la conexión con la API"""
    api_url = "http://localhost:5000/api/conexiones"
    
    try:
        print("🔍 Intentando conectar con la API...")
        response = requests.get(api_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n✅ Conexión exitosa!")
            print(f"📊 Total de registros: {data['count']}")
            
            # Mostrar tabla con los primeros 5 registros
            headers = ["Origen", "Destino", "Distancia (km)", "Adyacente"]
            table_data = [
                [item['origen'], item['destino'], item['distancia_km'], item['adyacente']] 
                for item in data['data'][:5]
            ]
            
            print("\n📋 Primeros 5 registros:")
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
            
            # Guardar datos completos en JSON
            with open('datos_conexiones.json', 'w', encoding='utf-8') as f:
                json.dump(data['data'], f, indent=2, ensure_ascii=False)
            print("\n💾 Datos guardados en 'datos_conexiones.json'")
            
        else:
            print(f"\n❌ Error en la API (Código {response.status_code}):")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("\n❌ No se pudo conectar al servidor. Verifica que:")
        print("- La API esté corriendo (ejecuta API.py primero)")
        print("- El puerto coincida (5000)")
        print("- No haya errores en la terminal donde corre la API")
        
    except requests.exceptions.Timeout:
        print("\n⌛ Tiempo de espera agotado")
        
    except Exception as e:
        print(f"\n⚠️ Error inesperado: {str(e)}")

if __name__ == "__main__":
    test_api()