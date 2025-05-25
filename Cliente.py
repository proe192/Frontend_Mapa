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
        self.page.title = "Rutas Quetzaltenango "
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 20
        self.page.window_width = 1200
        self.page.window_height = 800
        self.lugares = []
        self.grafo_completo = None

    def setup_ui(self):
        self.title = ft.Text("Sistema de Rutas Cortas", size=24, weight=ft.FontWeight.BOLD)
        self.dd_origen = ft.Dropdown(label="Origen", width=300, autofocus=True)
        self.dd_destino = ft.Dropdown(label="Destino", width=300)

        # CORREGIDO: íconos como string
        self.btn_calcular = ft.ElevatedButton("Calcular Ruta", icon="directions", on_click=self.calcular_ruta)
        self.btn_conectividad = ft.ElevatedButton("Verificar Conectividad", icon="check_circle_outline", on_click=self.verificar_conectividad)

        self.txt_resultado = ft.Text("", size=18)
        self.txt_distancia = ft.Text("", size=16)
        self.txt_camino = ft.Text("", size=14)
        self.txt_conectividad = ft.Text("", size=16)
        self.img_grafo = ft.Image(width=700, height=500, visible=False)

        self.page.add(
            ft.Column([
                ft.Row([self.title], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([self.dd_origen, self.dd_destino]),
                ft.Row([self.btn_calcular, self.btn_conectividad], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(),
                self.txt_resultado,
                self.txt_conectividad,
                self.txt_distancia,
                self.txt_camino,
                ft.Row([self.img_grafo], alignment=ft.MainAxisAlignment.CENTER)
            ], spacing=15)
        )

    def cargar_lugares(self):
        try:
            response = requests.get("http://localhost:5000/api/lugares")
            if response.status_code == 200:
                self.lugares = response.json().get("lugares", [])
                self.actualizar_dropdowns()
                self.construir_grafo_completo()
        except Exception as e:
            self.mostrar_mensaje(f"Error cargando lugares: {str(e)}", "red")

    def construir_grafo_completo(self):
        try:
            response = requests.get("http://localhost:5000/api/matrices")
            if response.status_code == 200:
                data = response.json()
                self.grafo_completo = nx.DiGraph()
                self.grafo_completo.add_nodes_from(data["lugares"])

                for i, origen in enumerate(data["lugares"]):
                    for j, destino in enumerate(data["lugares"]):
                        if data["matriz_adyacencia"][i][j] == 1:
                            distancia = requests.get(
                                f"http://localhost:5000/api/distancia?origen={origen}&destino={destino}"
                            ).json().get("distancia", 0)
                            self.grafo_completo.add_edge(origen, destino, weight=distancia)
        except Exception as e:
            print(f"Error construyendo grafo completo: {str(e)}")

    def actualizar_dropdowns(self):
        options = [ft.dropdown.Option(lugar) for lugar in self.lugares]
        self.dd_origen.options = options
        self.dd_destino.options = options
        self.page.update()

    def calcular_ruta(self, e):
        origen = self.dd_origen.value
        destino = self.dd_destino.value

        if not origen or not destino:
            self.mostrar_mensaje("Seleccione origen y destino", "red")
            return

        try:
            respuesta = requests.get(
                f"http://localhost:5000/api/camino-minimo?origen={origen}&destino={destino}"
            ).json()

            if "error" in respuesta:
                self.mostrar_mensaje(respuesta["error"], "red")
                return

            self.mostrar_resultados_ruta(respuesta)
            self.dibujar_grafo_con_ruta(respuesta["camino"])

        except Exception as e:
            self.mostrar_mensaje(f"Error: {str(e)}", "red")

    def verificar_conectividad(self, e):
        origen = self.dd_origen.value
        destino = self.dd_destino.value

        if not origen or not destino:
            self.mostrar_mensaje("Seleccione origen y destino", "red")
            return

        try:
            respuesta = requests.get(
                f"http://localhost:5000/api/conectividad?origen={origen}&destino={destino}"
            ).json()

            if "error" in respuesta:
                self.mostrar_mensaje(respuesta["error"], "red")
                return

            self.mostrar_resultados_conectividad(respuesta)

            if respuesta.get("conectado"):
                self.dibujar_grafo_completo(resaltar_origen=origen, resaltar_destino=destino)

        except Exception as e:
            self.mostrar_mensaje(f"Error: {str(e)}", "red")

    def mostrar_resultados_ruta(self, datos):
        self.txt_resultado.value = "✅ Ruta encontrada"
        self.txt_resultado.color = ft.colors.GREEN
        self.txt_distancia.value = f"Distancia total: {datos['distancia']} km"
        self.txt_camino.value = "Ruta: " + " → ".join(datos["camino"])
        self.txt_conectividad.value = ""
        self.page.update()

    def mostrar_resultados_conectividad(self, datos):
        conectado = datos.get("conectado", False)
        self.txt_resultado.value = "✅ Conectado" if conectado else "❌ No conectado"
        self.txt_resultado.color = "green" if conectado else ft.colors.RED
        self.txt_conectividad.value = "Conexión directa" if datos.get("conexion_directa") else "Conexión indirecta"
        self.txt_distancia.value = ""
        self.txt_camino.value = ""
        self.page.update()

    def dibujar_grafo_con_ruta(self, camino):
        if not self.grafo_completo:
            self.mostrar_mensaje("Grafo no disponible", "orange")
            return

        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(self.grafo_completo)

        nx.draw_networkx_nodes(self.grafo_completo, pos, node_size=700, node_color='lightgray')
        nx.draw_networkx_labels(self.grafo_completo, pos)
        nx.draw_networkx_edges(self.grafo_completo, pos, edge_color='gray', arrows=True)

        if len(camino) > 1:
            edges = [(camino[i], camino[i+1]) for i in range(len(camino)-1)]
            nx.draw_networkx_nodes(self.grafo_completo, pos, nodelist=camino, node_size=800, node_color='skyblue')
            nx.draw_networkx_edges(self.grafo_completo, pos, edgelist=edges, edge_color='red', width=3, arrows=True)

        self.mostrar_grafo_en_ui()

    def dibujar_grafo_completo(self, resaltar_origen=None, resaltar_destino=None):
        if not self.grafo_completo:
            return

        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(self.grafo_completo)

        node_colors = []
        for node in self.grafo_completo.nodes():
            if node == resaltar_origen:
                node_colors.append('green')
            elif node == resaltar_destino:
                node_colors.append('red')
            else:
                node_colors.append('lightgray')

        nx.draw_networkx_nodes(self.grafo_completo, pos, node_size=700, node_color=node_colors)
        nx.draw_networkx_labels(self.grafo_completo, pos)
        nx.draw_networkx_edges(self.grafo_completo, pos, edge_color='gray', arrows=True)

        self.mostrar_grafo_en_ui()

    def mostrar_grafo_en_ui(self):
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close()
        buf.seek(0)

        self.img_grafo.src_base64 = base64.b64encode(buf.read()).decode("utf-8")
        self.img_grafo.visible = True
        self.page.update()

    def mostrar_mensaje(self, mensaje, color):
        self.txt_resultado.value = mensaje
        self.txt_resultado.color = color
        self.txt_distancia.value = ""
        self.txt_camino.value = ""
        self.txt_conectividad.value = ""
        self.page.update()

def main(page: ft.Page):
    FletGrafoApp(page)

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
