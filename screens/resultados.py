"""Pantalla de resultados al terminar la ronda.

A la izquierda, cómo le fue a cada jugador; a la derecha, hasta dónde llegó la
misión, cómo terminó el caso del infiltrado y cuántos logros consiguieron.
Abajo, dos botones: "Ver logros" (el árbol completo, screens/logros.py) y
"Volver al menú". La lógica de la pantalla está en App._tecla_resultados.
"""

import pygame


from fuentes import fuente_de_tamano
from ui_components import Button, dibujar_texto_ajustado


COLOR_FONDO = (26, 28, 48)
COLOR_TITULO = (255, 214, 64)
COLOR_TEXTO = (245, 246, 252)
COLOR_TENUE = (170, 178, 214)
COLOR_BARRA = (96, 188, 118)
COLOR_BARRA_MALA = (214, 74, 68)


def opciones_resultados(logros):
    """(texto, acción) de los botones de abajo."""
    opciones = []
    if logros is not None:
        opciones.append((f"Ver logros  {logros.arbol.obtenidos()}/{logros.arbol.total()}", "logros"))
    opciones.append(("Volver al menú", "menu"))
    return opciones


def render_resultados(screen, jugadores, font=None, small_font=None,
                      mision=None, equipo=None, infiltrado=None, logros=None, seleccion=0):
    """Dibuja el resumen. Devuelve los rects de los botones (para el mouse)."""
    screen.fill(COLOR_FONDO)
    ancho, alto = screen.get_size()
    f = fuente_de_tamano(max(14, min(22, ancho // 62)))
    titulo_f = font or fuente_de_tamano(30)
    paso = f.get_linesize() + 6

    titulo, color = "SE ACABÓ LA RONDA", COLOR_TEXTO
    if mision is not None and mision.activa:
        if mision.resultado == "victoria":
            titulo, color = "¡ESCAPARON DE LA NAVE!", COLOR_BARRA
        else:
            titulo, color = "NO LOGRARON ESCAPAR", COLOR_BARRA_MALA
    encabezado = titulo_f.render(titulo, True, color)
    screen.blit(encabezado, encabezado.get_rect(center=(ancho // 2, 56)))
    if equipo is not None:
        sub = f.render(f"Puntos del equipo: {equipo.total}", True, COLOR_TITULO)
        screen.blit(sub, sub.get_rect(center=(ancho // 2, 92)))

    columna = ancho // 2

    # -- Jugadores --------------------------------------------------------------
    y = 130
    screen.blit(f.render("Cómo le fue a cada uno", True, COLOR_TITULO), (60, y))
    y += paso + 6

    ordenados = sorted(jugadores, key=lambda j: j.puntos, reverse=True)
    for puesto, jugador in enumerate(ordenados, start=1):
        linea = f"{puesto}.  {jugador.rol}  —  {jugador.puntos} pts"
        screen.blit(f.render(linea, True, COLOR_TEXTO), (80, y))
        y += paso

        detalle = f"tareas hechas: {jugador.tareas_hechas}"
        screen.blit(f.render(detalle, True, COLOR_TENUE), (110, y))
        y += paso

        camino = [n.nombre for n in jugador.arbol.desbloqueadas()] if not jugador.arbol.vacio else []
        if camino:
            screen.blit(f.render("rama: " + " > ".join(camino), True, COLOR_TENUE), (110, y))
        else:
            screen.blit(f.render("sin árbol de habilidades definido", True, COLOR_TENUE), (110, y))
        y += paso + 14

    # -- La misión ----------------------------------------------------------------
    y = 130
    screen.blit(f.render("La misión", True, COLOR_TITULO), (columna + 40, y))
    y += paso + 6
    if mision is not None and mision.activa:
        from mision import PIEZAS_NECESARIAS
        fases = {"prision": "seguían en la prisión", "sabotaje": "apagando las consolas",
                 "capsula": "llevando piezas a la cápsula", "reparar": "reparando la cápsula",
                 "huida": "corriendo a la cápsula"}
        lineas = ["Escaparon de la nave." if mision.resultado == "victoria"
                  else f"Se quedaron {fases.get(mision.fase, mision.fase)}.",
                  f"Piezas en la cápsula: {mision.piezas_entregadas}/{PIEZAS_NECESARIAS}"]
        if logros is not None:
            lineas.append(f"Veces que los atraparon: {logros.capturas_total}")
        eliminados = [j.rol for j in jugadores if getattr(j, "eliminado", False)]
        lineas.append("Eliminados: " + (", ".join(eliminados) if eliminados else "nadie"))
        for linea in lineas:
            dibujar_texto_ajustado(screen, linea, f, columna + 60, y, ancho - columna - 80, COLOR_TEXTO)
            y += paso

    # Misión secundaria del infiltrado (infiltrado.py): cómo terminó.
    resumen = infiltrado.resumen() if infiltrado is not None else None
    if resumen:
        color = COLOR_BARRA if infiltrado.estado == "expuesto" else COLOR_TENUE
        dibujar_texto_ajustado(screen, resumen, f, columna + 40, y + 6, ancho - columna - 60, color)
        y += paso
    if logros is not None:
        texto = f"Logros: {logros.arbol.obtenidos()}/{logros.arbol.total()}"
        screen.blit(f.render(texto, True, COLOR_TITULO), (columna + 40, y + 6))

    # -- Botones ------------------------------------------------------------------
    opciones = opciones_resultados(logros)
    alto_boton = 52 if alto >= 600 else 40
    ancho_boton = min(360, (ancho - 80) // len(opciones) - 20)
    separacion = 28
    total = len(opciones) * ancho_boton + (len(opciones) - 1) * separacion
    x = ancho // 2 - total // 2
    y_botones = alto - alto_boton - 46
    mouse = pygame.mouse.get_pos()
    rects = []
    for i, (texto, accion) in enumerate(opciones):
        rect = pygame.Rect(x, y_botones, ancho_boton, alto_boton)
        Button(rect, texto, accion).draw(screen, hover=(i == seleccion or rect.collidepoint(mouse)))
        rects.append(rect)
        x += ancho_boton + separacion
    pista = fuente_de_tamano(15).render("Flechas + Enter  ·  Mando: cruceta y A", True, COLOR_TENUE)
    screen.blit(pista, pista.get_rect(midtop=(ancho // 2, y_botones + alto_boton + 12)))
    return rects
