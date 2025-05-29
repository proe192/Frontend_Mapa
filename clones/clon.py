import flet as ft
import requests
import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import matplotlib
import math
matplotlib.use('Agg')  # Esto soluciona el problema del hilo

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
        self.lugares = []
        self.grafo_completo = None
        self._node_positions = None  # Para cachear posiciones

    def setup_ui(self):
        self.title = ft.Text("Sistema de Rutas Cortas", size=24, weight=ft.FontWeight.BOLD)
        self.dd_origen = ft.Dropdown(label="Origen", width=300, autofocus=True)
        self.dd_destino = ft.Dropdown(label="Destino", width=300)

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
                            try:
                                distancia_response = requests.get(
                                    f"http://localhost:5000/api/distancia?origen={origen}&destino={destino}"
                                )
                                if distancia_response.status_code == 200:
                                    distancia = distancia_response.json().get("distancia", 0)
                                    self.grafo_completo.add_edge(origen, destino, weight=distancia)
                            except Exception as e:
                                print(f"Error obteniendo distancia entre {origen} y {destino}: {str(e)}")
        except Exception as e:
            print(f"Error construyendo grafo completo: {str(e)}")

    def actualizar_dropdowns(self):
        if not self.lugares:
            return
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
        self.txt_resultado.color = "green"
        self.txt_distancia.value = f"Distancia total: {datos['distancia']} km"
        self.txt_camino.value = "Ruta: " + " → ".join(datos["camino"])
        self.txt_conectividad.value = ""
        self.page.update()

    def mostrar_resultados_conectividad(self, datos):
        conectado = datos.get("conectado", False)
        self.txt_resultado.value = "✅ Conectado" if conectado else "❌ No conectado"
        self.txt_resultado.color = "green" if conectado else "red"
        self.txt_conectividad.value = "Conexión directa" if datos.get("conexion_directa") else "Conexión indirecta"
        self.txt_distancia.value = ""
        self.txt_camino.value = ""
        self.page.update()

    def _get_node_positions(self):
        if self._node_positions is None and self.grafo_completo:
            # Crear posiciones fijas muy esparcidas
            nodes = list(self.grafo_completo.nodes())
            num_nodes = len(nodes)
            self._node_positions = {}
            
            # Posiciones predefinidas para las esquinas y centro
            fixed_positions = {
                0: (0, 0),    # Esquina inferior izquierda
                1: (1, 0),     # Esquina inferior derecha
                2: (1, 1),     # Esquina superior derecha
                3: (0, 1),     # Esquina superior izquierda
                4: (0.5, 0.5)  # Centro exacto
            }
            
            # Asignar las posiciones fijas a los primeros nodos
            for i, pos in fixed_positions.items():
                if i < num_nodes:
                    self._node_positions[nodes[i]] = pos
            
            # Distribuir el resto de nodos en círculos concéntricos
            for i in range(len(fixed_positions), num_nodes):
                # Calcular ángulo y radio para posición circular
                angle = 2 * math.pi * (i - len(fixed_positions)) / (num_nodes - len(fixed_positions))
                radius = 0.4 + 0.3 * ((i % 3) / 2)  # Variar el radio
                
                # Coordenadas polares a cartesianas
                x = 0.5 + radius * math.cos(angle)
                y = 0.5 + radius * math.sin(angle)
                
                # Ajustar para que no queden demasiado cerca del centro
                if abs(x - 0.5) < 0.2:
                    x = 0.5 + 0.3 * (1 if x > 0.5 else -1)
                if abs(y - 0.5) < 0.2:
                    y = 0.5 + 0.3 * (1 if y > 0.5 else -1)
                
                self._node_positions[nodes[i]] = (x, y)
        
        return self._node_positions

    def dibujar_grafo_con_ruta(self, camino=None):
        if not self.grafo_completo:
            self.mostrar_mensaje("Grafo no disponible", "red")
            return

        plt.figure(figsize=(12, 8))
        plt.clf()  # Limpiar figura antes de dibujar

        # Obtener posiciones muy esparcidas
        pos = self._get_node_positions()

        # Dibujar todos los nodos
        nx.draw_networkx_nodes(
            self.grafo_completo, pos,
            node_size=2500,
            node_color="blue",
            alpha=0.7
        )

        # Etiquetas de nodos
        nx.draw_networkx_labels(
            self.grafo_completo, pos,
            font_size=10,
            font_weight="bold",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.7)
        )

        # Todas las conexiones (grises)
        nx.draw_networkx_edges(
            self.grafo_completo, pos,
            edge_color="lightgray",
            arrows=True,
            arrowstyle="->",
            arrowsize=15,
            width=1.0,
            alpha=0.5
        )

        # Etiquetas de distancia
        edge_labels = nx.get_edge_attributes(self.grafo_completo, "weight")
        nx.draw_networkx_edge_labels(
            self.grafo_completo, pos,
            edge_labels=edge_labels,
            font_size=8,
            label_pos=0.5
        )

        # Resaltar la ruta si existe
        if camino and len(camino) > 1:
            edges = [(camino[i], camino[i + 1]) for i in range(len(camino) - 1)]
            
            # Resaltar nodos de la ruta
            nx.draw_networkx_nodes(
                self.grafo_completo, pos,
                nodelist=camino,
                node_size=2500,
                node_color="skyblue",
                edgecolors="blue",
                linewidths=2
            )
            
            # Resaltar conexiones de la ruta
            nx.draw_networkx_edges(
                self.grafo_completo, pos,
                edgelist=edges,
                edge_color="red",
                width=3,
                arrows=True,
                arrowstyle="->",
                arrowsize=20
            )

        # Ajustar los márgenes para que no se corten los nodos de las esquinas
        plt.xlim(-0.15, 1.15)
        plt.ylim(-0.15, 1.15)
        plt.axis('off')  # Ocultar ejes

        self.mostrar_grafo_en_ui()

    def dibujar_grafo_completo(self, resaltar_origen=None, resaltar_destino=None):
        if not self.grafo_completo:
            return

        plt.figure(figsize=(12, 8))
        plt.clf()  # Limpiar figura antes de dibujar

        # Obtener posiciones muy esparcidas
        pos = self._get_node_positions()

        # Colores para los nodos
        node_colors = []
        for node in self.grafo_completo.nodes():
            if node == resaltar_origen:
                node_colors.append("green")
            elif node == resaltar_destino:
                node_colors.append("red")
            else:
                node_colors.append("lightblue")

        # Dibujar todos los nodos
        nx.draw_networkx_nodes(
            self.grafo_completo, pos,
            node_size=2500,
            node_color=node_colors,
            alpha=0.7
        )

        # Etiquetas de nodos
        nx.draw_networkx_labels(
            self.grafo_completo, pos,
            font_size=10,
            font_weight="bold",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.7)
        )

        # Todas las conexiones
        nx.draw_networkx_edges(
            self.grafo_completo, pos,
            edge_color="gray",
            arrows=True,
            arrowstyle="->",
            arrowsize=15,
            width=1.5
        )

        # Etiquetas de distancia
        edge_labels = nx.get_edge_attributes(self.grafo_completo, "weight")
        nx.draw_networkx_edge_labels(
            self.grafo_completo, pos,
            edge_labels=edge_labels,
            font_size=8,
            label_pos=0.5
        )

        # Ajustar los márgenes para que no se corten los nodos de las esquinas
        plt.xlim(-0.15, 1.15)
        plt.ylim(-0.15, 1.15)
        plt.axis('off')  # Ocultar ejes

        self.mostrar_grafo_en_ui()

    def mostrar_grafo_en_ui(self):
        buf = BytesIO()
        plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
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

