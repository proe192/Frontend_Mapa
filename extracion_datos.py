import flet as ft
import requests
import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO
import base64

class FletGrafoApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.setup_config()
        self.setup_ui()
        self.cargar_lugares()

    def setup_config(self):
        self.page.title = "Rutas Quetzaltenango"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 20
        self.page.window_width = 1200
        self.page.window_height = 800

    def setup_ui(self):
        """Configura los componentes de la interfaz"""
        self.title = ft.Text("Sistema de Rutas Cortas", size=24, weight=ft.FontWeight.BOLD)
        
        # Controles de selección
        self.dd_origen = ft.Dropdown(label="Origen", width=300)
        self.dd_destino = ft.Dropdown(label="Destino", width=300)
        
        # Botones
        self.btn_conectividad = ft.ElevatedButton(
            "Verificar Conectividad",
            icon=ft.icons.CHECK_CIRCLE_OUTLINE,
            on_click=self.verificar_conectividad
        )
        self.btn_ruta = ft.ElevatedButton(
            "Calcular Ruta",
            icon=ft.icons.DIRECTIONS,
            on_click=self.calcular_ruta
        )
        
        # Área de resultados
        self.txt_resultado = ft.Text("", size=18)
        self.txt_detalles = ft.Text("", size=14)
        
        # Gráfico
        self.img_grafo = ft.Image(width=700, height=500)
        
        # Diseño principal
        self.page.add(
            ft.Column([
                ft.Row([self.title], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([self.dd_origen, self.dd_destino]),
                ft.Row([self.btn_conectividad, self.btn_ruta], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(),
                self.txt_resultado,
                self.txt_detalles,
                ft.Row([self.img_grafo], alignment=ft.MainAxisAlignment.CENTER)
            ], spacing=15)
        )

    def cargar_lugares(self):
        """Carga los lugares desde la API"""
        try:
            response = requests.get("http://localhost:5000/api/lugares")
            if response.status_code == 200:
                lugares = response.json().get("lugares", [])
                self.dd_origen.options = [ft.dropdown.Option(lugar) for lugar in lugares]
                self.dd_destino.options = [ft.dropdown.Option(lugar) for lugar in lugares]
                self.page.update()
        except Exception as e:
            self.mostrar_mensaje(f"Error cargando lugares: {str(e)}", ft.colors.RED)

    def verificar_conectividad(self, e):
        origen = self.dd_origen.value
        destino = self.dd_destino.value
        
        if not origen or not destino:
            self.mostrar_mensaje("Seleccione origen y destino", ft.colors.RED)
            return
        
        try:
            response = requests.get(
                f"http://localhost:5000/api/conectividad?origen={origen}&destino={destino}"
            )
            resultado = response.json()
            
            if "error" in resultado:
                self.mostrar_mensaje(resultado["error"], ft.colors.RED)
                return
            
            color = ft.colors.GREEN if resultado["conectado"] else ft.colors.RED
            mensaje = "✅ CONECTADOS" if resultado["conectado"] else "❌ NO CONECTADOS"
            
            self.txt_resultado.value = mensaje
            self.txt_resultado.color = color
            self.txt_detalles.value = f"Entre {origen} y {destino}"
            self.page.update()
            
        except Exception as e:
            self.mostrar_mensaje(f"Error: {str(e)}", ft.colors.RED)

    def calcular_ruta(self, e):
        origen = self.dd_origen.value
        destino = self.dd_destino.value
        
        if not origen or not destino:
            self.mostrar_mensaje("Seleccione origen y destino", ft.colors.RED)
            return
        
        try:
            response = requests.get(
                f"http://localhost:5000/api/camino-minimo?origen={origen}&destino={destino}"
            )
            resultado = response.json()
            
            if "error" in resultado:
                self.mostrar_mensaje(resultado["error"], ft.colors.RED)
                return
            
            self.mostrar_resultado_ruta(resultado)
            self.dibujar_ruta(resultado["camino"])
            
        except Exception as e:
            self.mostrar_mensaje(f"Error: {str(e)}", ft.colors.RED)

    def mostrar_resultado_ruta(self, resultado):
        self.txt_resultado.value = "✅ RUTA ENCONTRADA"
        self.txt_resultado.color = ft.colors.GREEN
        self.txt_detalles.value = (
            f"De {resultado['origen']} a {resultado['destino']}\n"
            f"Distancia: {resultado['distancia']} km\n"
            f"Camino: {' → '.join(resultado['camino'])}"
        )
        self.page.update()

    def dibujar_ruta(self, camino):
        """Dibuja el grafo con la ruta resaltada"""
        G = nx.DiGraph()
        
        # Agregar todos los nodos
        G.add_nodes_from(self.dd_origen.options)
        
        # Agregar la ruta encontrada
        for i in range(len(camino)-1):
            G.add_edge(camino[i], camino[i+1])
        
        # Dibujar
        pos = nx.spring_layout(G)
        plt.figure(figsize=(10, 6))
        
        # Dibujar nodos
        nx.draw_networkx_nodes(G, pos, node_size=700, node_color='lightblue')
        
        # Dibujar la ruta resaltada
        if len(camino) > 1:
            edges = [(camino[i], camino[i+1]) for i in range(len(camino)-1)]
            nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color='red', width=3, arrows=True)
        
        nx.draw_networkx_labels(G, pos)
        
        # Convertir a imagen para Flet
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close()
        buf.seek(0)
        
        self.img_grafo.src_base64 = base64.b64encode(buf.read()).decode("utf-8")
        self.page.update()

    def mostrar_mensaje(self, mensaje, color):
        self.txt_resultado.value = mensaje
        self.txt_resultado.color = color
        self.txt_detalles.value = ""
        self.page.update()

def main(page: ft.Page):
    app = FletGrafoApp(page)

if __name__ == "__main__":
    ft.app(target=main)