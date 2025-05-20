import flet as ft

def main(page: ft.Page):
    page.title = "RUTAS QUETZALTENANGO"
    page.window_centered = True
    page.window_width = 800
    page.window_height = 600
    page.bgcolor = "#284D70"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.END  # Página alineada a la derecha

    # Campos de texto
    inicio = ft.TextField(
        label='Inicio',
        width=200,
        bgcolor=ft.Colors.WHITE,
        border_color=ft.Colors.BLACK,
        label_style=ft.TextStyle(color=ft.Colors.BLACK),
        hint_style=ft.TextStyle(color=ft.Colors.BLACK),
        text_style=ft.TextStyle(color=ft.Colors.BLACK)
    )
    
    destino = ft.TextField(
        label='Destino',
        width=200,
        bgcolor=ft.Colors.WHITE,
        border_color=ft.Colors.BLACK,
        label_style=ft.TextStyle(color=ft.Colors.BLACK),
        hint_style=ft.TextStyle(color=ft.Colors.BLACK),
        text_style=ft.TextStyle(color=ft.Colors.BLACK)
    )

    # Texto del mensaje
    mensaje = ft.Text("", size=14, weight=ft.FontWeight.BOLD)

    # Acción del botón
    def btn_ruta(e):
        if inicio.value.strip() == '':
            mensaje.value = "Por favor ingrese una ruta válida"
            mensaje.color = ft.Colors.RED
        else:
            mensaje.value = f"Ruta calculada: {inicio.value} → {destino.value}"
            mensaje.color = ft.Colors.WHITE
        page.update()

    # Botón
    btnRuta = ft.ElevatedButton(
        text='CALCULAR RUTA',
        on_click=btn_ruta,
        color=ft.Colors.WHITE,
        bgcolor="#39700D",
        height=45,
        width=180,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=15
        ),
        icon=ft.Icons.DIRECTIONS,
        icon_color=ft.Colors.WHITE
    )

    # Layout principal
    page.add(
        ft.Column(
            [
                ft.Row(
                    [inicio, destino, btnRuta],
                    spacing=15,
                    alignment=ft.MainAxisAlignment.END,
                    width=page.window_width - 40
                ),
                ft.Row(  # Mensaje alineado a la derecha
                    [
                        ft.Container(
                            content=mensaje,
                            padding=10,
                            bgcolor=ft.Colors.WHITE24,
                            border_radius=10,
                        )
                    ],
                    alignment=ft.MainAxisAlignment.END,
                    width=page.window_width - 40
                )
            ],
            expand=True,
            spacing=20,
            alignment=ft.MainAxisAlignment.START
        )
    )

ft.app(target=main)

