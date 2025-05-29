
import flet as ft
import requests
import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import matplotlib
matplotlib.use('Agg')

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
        self._node_positions = None

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

        self.page.add(ft.Column([
            ft.Row([self.title], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([self.dd_origen, self.dd_destino]),
            ft.Row([self.btn_calcular, self.btn_conectividad], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(),
            self.txt_resultado,
            self.txt_conectividad,
            self.txt_distancia,
            self.txt_camino,
            ft.Row([self.img_grafo], alignment=ft.MainAxisAlignment.CENTER)
        ], spacing=15))

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
            self._node_positions = {
                "DF la esperanza": (0.02, 0.84),
                "interplaza Xela": (0.13, 0.76),
                "Umg": (0.16, 0.84),
                "Col el Maestro": (0.19, 0.99),
                "hospital": (0.34, 0.79),
                "suma": (0.31, 0.97),
                "parque la floresta": (0.39, 0.61),
                "seminario san jose": (0.32, 0.53),
                "paseo luna": (0.21, 1.15),
                "salon comunal": (0.27, 1.26),
                "Xelapan los trigales": (0.53, 1.10),
                "Monumento a Tecun uman": (0.53, 0.95),
                "pradera xela": (0.43, 0.53),
                "Xelapan los altos": (0.55, 0.59),
                "CUNOC-USAC": (0.43, 0.40),
                "Complejo deportivo": (0.49, 0.46),
                "Iglesia el Calvario": (0.53, 0.29),
                "Hospital Rodolfo Robles": (0.50, 0.18),
                "La Cantera Sport Club": (0.46, 0.00),
                "Utz Ulew Mall": (0.57, 0.40),
                "benito juares": (0.65, 0.42),
                "Estadio Mario Camposeco": (0.71, 0.37),
                "Centro de atencion Permanente quetzaltenango": (0.76, 0.52),
                "Col El Rosario": (0.81, 0.65),
                "col san antonio": (0.76, 0.85),
                "Parque a Centroamerica": (0.84, 0.34),
                "plaza 7": (0.89, 0.24),
                "IGSS Quetzaltenango": (1.00, 0.37),
                "Monumento a la Marimba": (0.93, 0.41),
                "Parque Colonia Molina": (0.97, 0.31),
                "VFH6+H74 Aldea Justo Rufino Barrios": (0.10, 0.60)
            }
            for node in self.grafo_completo.nodes():
                if node not in self._node_positions:
                    self._node_positions[node] = (0.5, 0.5)
        return self._node_positions

    def dibujar_grafo_con_ruta(self, camino=None):
        if not self.grafo_completo:
            self.mostrar_mensaje("Grafo no disponible", "red")
            return

        plt.figure(figsize=(20, 16))
        plt.clf()
        pos = self._get_node_positions()
          #modificar aqui
        nx.draw_networkx_nodes(self.grafo_completo, pos, node_size=3500, node_color="lightgreen", alpha=0.9, edgecolors="blue", linewidths=1)
        nx.draw_networkx_labels(self.grafo_completo, pos, font_size=12, font_weight="bold", font_color="black", bbox=dict(alpha=0))
        nx.draw_networkx_edges(self.grafo_completo, pos, edge_color="gray", arrows=True, arrowstyle="->", arrowsize=10, width=1.0, alpha=0.5)

        edge_labels = {}
        for edge in self.grafo_completo.edges():
            if abs(pos[edge[0]][0] - pos[edge[1]][0]) < 0.5 and abs(pos[edge[0]][1] - pos[edge[1]][1]) < 0.5:
                edge_labels[edge] = self.grafo_completo.edges[edge]['weight']
        nx.draw_networkx_edge_labels(self.grafo_completo, pos, edge_labels=edge_labels, font_size=7, label_pos=0.5, bbox=dict(facecolor="white", alpha=0.6, edgecolor="none"))

        if camino and len(camino) > 1:
            edges = [(camino[i], camino[i+1]) for i in range(len(camino)-1)]
            nx.draw_networkx_nodes(self.grafo_completo, pos, nodelist=camino, node_size=1500, node_color="lightgreen", edgecolors="darkblue", linewidths=2)
            nx.draw_networkx_edges(self.grafo_completo, pos, edgelist=edges, edge_color="red", width=2.5, arrows=True, arrowstyle="->", arrowsize=15)

        plt.xlim(-0.1, 1.1)
        plt.ylim(-0.1, 1.4)
        plt.axis('off')
        plt.tight_layout()
        self.mostrar_grafo_en_ui()

    def dibujar_grafo_completo(self, resaltar_origen=None, resaltar_destino=None):
        if not self.grafo_completo:
            return

        plt.figure(figsize=(20, 16))
        plt.clf()
        pos = self._get_node_positions()

        node_colors = []
        for n in self.grafo_completo.nodes():
            if n == resaltar_origen:
                node_colors.append("green")
            elif n == resaltar_destino:
                node_colors.append("red")
            else:
                node_colors.append("lightgreen")
              #modificacion aqui
        nx.draw_networkx_nodes(self.grafo_completo, pos, node_size=3500, node_color=node_colors, alpha=0.9, edgecolors="blue", linewidths=1)
        nx.draw_networkx_labels(self.grafo_completo, pos, font_size=12, font_weight="bold", font_color="black", bbox=dict(alpha=0))

        visible_edges = []
        for edge in self.grafo_completo.edges():
            if abs(pos[edge[0]][0] - pos[edge[1]][0]) < 0.5 and abs(pos[edge[0]][1] - pos[edge[1]][1]) < 0.5:
                visible_edges.append(edge)

        nx.draw_networkx_edges(self.grafo_completo, pos, edgelist=visible_edges, edge_color="gray", arrows=True, arrowstyle="->", arrowsize=10, width=1.5, alpha=0.7)

        edge_labels = {}
        for edge in visible_edges:
            edge_labels[edge] = self.grafo_completo.edges[edge]['weight']
        nx.draw_networkx_edge_labels(self.grafo_completo, pos, edge_labels=edge_labels, font_size=7, label_pos=0.5, bbox=dict(facecolor="white", alpha=0.6, edgecolor="none"))

        plt.xlim(-0.1, 1.1)
        plt.ylim(-0.1, 1.4)
        plt.axis('off')
        plt.tight_layout()
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
