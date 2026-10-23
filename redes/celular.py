"""El celular de cada jugador: las pantallas de NEXUS y qué hace cada opción.

El celular es un panel más del jugador (jugador.panel con tipo "celular"):
mientras lo tiene abierto no camina, y si un alien llega, lo atrapa. Lo que
pasa en la red (rumores, desmentidos, el grafo) está en nexus.py; aquí solo
se arman las pantallas y se resuelve la opción elegida. El dibujo está en
screens/celular.py.

Pantallas ("vista"):
    feed       lo que le llegó por NEXUS, lo más nuevo arriba
    post       una publicación, con lo que se puede hacer con ella
    origen     de dónde vino un rumor (camino más corto desde quien lo empezó)
    ubicacion  publicar la foto tal cual (se ve dónde estás) o recortada
    mensaje    el resultado de lo que hizo
"""

from redes.nexus import COLOR_BIEN, COLOR_MAL


def abrir(juego, jugador):
    if juego.nexus is None:
        jugador.avisar("No hay señal de NEXUS en este mapa.", COLOR_MAL)
        return
    jugador.abrir_panel(_feed(juego, jugador))
    if juego.logros is not None:
        juego.logros.conseguir("conectado", jugador)


def volver(juego, jugador):
    """La tecla de celular con el celular abierto: atrás, o cerrar desde el feed."""
    panel = jugador.panel or {}
    if panel.get("vista") in (None, "feed"):
        jugador.cerrar_panel()
    else:
        jugador.abrir_panel(_feed(juego, jugador))


def opciones_feed(juego, jugador):
    """Primero las fotos que tiene para publicar; después el feed."""
    red = juego.nexus
    opciones = [("foto", rumor) for rumor in red.evidencias.get(jugador, [])]
    opciones += [("post", pub) for pub in red.feed(jugador)]
    return opciones


def _feed(juego, jugador):
    return {"tipo": "celular", "vista": "feed", "opciones": opciones_feed(juego, jugador)}


def _post(juego, jugador, pub, camino=None):
    red = juego.nexus
    red.vistas[jugador].add(pub.id)
    acciones = []
    if pub.tipo == "rumor" and not pub.desmentida:
        if pub in red.evidencias.get(jugador, []):
            acciones.append(("Desmentir con mi foto", "desmentir"))
        elif red.investigando.get(jugador) is not pub:
            acciones.append(("Ir a verificarlo", "investigar"))
        else:
            acciones.append(("Dejar de investigarlo", "no_investigar"))
    if pub.tipo == "trampa" and not pub.reportada:
        if red.investigando.get(jugador) is not pub:
            acciones.append(("Ir allá", "investigar"))
        else:
            acciones.append(("Dejar de ir", "no_investigar"))
    if pub.autor != red.nodo_de(jugador):
        acciones.append(("Compartir", "compartir"))
    if pub.tipo in ("rumor", "trampa"):
        via = red.via(jugador, pub)
        if via in red.grafo and via != red.nodo_de(jugador):
            acciones.append((f"Reportar a {red.usuario(via)}", "reportar_via"))
        acciones.append(("¿De dónde salió esto?", "rastrear"))
    acciones.append(("Volver", "volver"))
    return {"tipo": "celular", "vista": "post", "pub": pub, "opciones": acciones,
            "camino": camino}


def _mensaje(texto, puntos, color=None):
    return {"tipo": "celular", "vista": "mensaje", "texto": texto, "puntos": puntos,
            "color": color or (COLOR_BIEN if puntos >= 0 else COLOR_MAL),
            "opciones": [("Volver al inicio", "volver")]}


def confirmar(juego, jugador):
    """El jugador eligió la opción del cursor."""
    red = juego.nexus
    panel = jugador.panel
    if red is None or panel is None:
        jugador.cerrar_panel()
        return
    opciones = panel.get("opciones", [])
    if not opciones:
        if panel.get("vista") != "feed":
            jugador.abrir_panel(_feed(juego, jugador))
        return
    eleccion = opciones[jugador.cursor % len(opciones)]
    vista = panel["vista"]

    if vista == "feed":
        tipo, dato = eleccion
        if tipo == "foto":
            jugador.abrir_panel({"tipo": "celular", "vista": "ubicacion", "rumor": dato,
                                 "opciones": [("Publicar la foto tal cual", "tal_cual"),
                                              ("Recortar el fondo y publicar", "recortada"),
                                              ("Volver", "volver")]})
        else:
            jugador.abrir_panel(_post(juego, jugador, dato))
        return

    accion = eleccion[1]
    if accion == "volver":
        jugador.abrir_panel(_feed(juego, jugador))
        return

    if vista == "ubicacion":
        texto, puntos = red.desmentir(jugador, panel["rumor"], accion == "tal_cual")
        jugador.tareas_hechas += 1
        jugador.abrir_panel(_mensaje(texto, puntos))
        return

    if vista == "origen":
        if accion == "reportar_origen":
            texto, puntos = red.reportar(jugador, panel["origen"])
            jugador.abrir_panel(_mensaje(texto, puntos))
        elif accion == "reportar_suplantacion":
            texto, puntos = red.reportar_suplantacion(jugador, panel["pub"])
            jugador.abrir_panel(_mensaje(texto, puntos))
        return

    pub = panel["pub"]
    if accion == "investigar":
        texto = red.investigar(jugador, pub)
        jugador.abrir_panel(_mensaje(texto, 0, (120, 190, 255)))
    elif accion == "no_investigar":
        red.investigando.pop(jugador, None)
        jugador.abrir_panel(_post(juego, jugador, pub))
    elif accion == "desmentir":
        jugador.abrir_panel({"tipo": "celular", "vista": "ubicacion", "rumor": pub,
                             "opciones": [("Publicar la foto tal cual", "tal_cual"),
                                          ("Recortar el fondo y publicar", "recortada"),
                                          ("Volver", "volver")]})
    elif accion == "compartir":
        texto, puntos = red.compartir(jugador, pub)
        jugador.abrir_panel(_mensaje(texto, puntos))
    elif accion == "reportar_via":
        texto, puntos = red.reportar(jugador, red.via(jugador, pub))
        jugador.abrir_panel(_mensaje(texto, puntos))
    elif accion == "rastrear":
        camino = red.rastrear(jugador, pub)
        origen = camino[0] if camino else pub.autor
        opciones = []
        if pub.suplantada and not pub.reportada:
            opciones.append((f"Reportar suplantación de {red.usuario(origen)}",
                             "reportar_suplantacion"))
        elif origen in red.grafo and origen != red.nodo_de(jugador):
            opciones.append((f"Reportar a {red.usuario(origen)}", "reportar_origen"))
        opciones.append(("Volver", "volver"))
        jugador.abrir_panel({"tipo": "celular", "vista": "origen", "pub": pub,
                             "camino": camino, "origen": origen, "opciones": opciones})


# -- Central de ayuda: lo que muestran las Terminales NEXUS del mapa ----------------------

def _pie(jugador):
    return (f"[{jugador.pista_mover()}] elegir   "
            f"[{jugador.nombre_tecla('interactuar')}] confirmar")


def lineas_estado(juego):
    """Cómo va el equipo en NEXUS, para la central de ayuda."""
    from data.nexus import NOMBRE_LUGAR, UMBRAL_PLANOS
    red = juego.nexus
    if red is None:
        return ["NEXUS no tiene señal en este mapa."]
    verde, rojo = red.barras()
    lineas = [f"Confianza de la tripulación: {int(verde * 100)}% en ustedes, "
              f"{int(rojo * 100)}% en los aliens."]
    if red.planos:
        lineas.append("Ya tienen los planos de la cápsula.")
    else:
        falta = max(0, int(round((getattr(red, "umbral_planos", UMBRAL_PLANOS) - verde) * 100)))
        lineas.append(f"Planos de la cápsula: les falta {falta}% de confianza.")
    activos = red.rumores_activos()
    if activos:
        lugares = ", ".join(NOMBRE_LUGAR.get(p.rumor["lugar"], "?") for p in activos)
        lineas.append(f"Rumores sin desmentir: {len(activos)} ({lugares}).")
    else:
        lineas.append("No hay rumores sin desmentir. Por ahora.")
    if rojo > verde:
        lineas.append("Los aliens van ganando en NEXUS: están más rápidos y ven más lejos.")
    return lineas


def panel_ayuda(juego, jugador, zona=None):
    """Menú de la central de ayuda de una Terminal NEXUS."""
    from data.nexus import AYUDA_TEMAS
    opciones = [(titulo, ("tema", i)) for i, (titulo, _) in enumerate(AYUDA_TEMAS)]
    opciones.append(("Repasar el tutorial", ("tutorial", None)))
    if getattr(juego, "infiltrado", None) is not None:
        opciones.append(("El caso del Cambiaformas", ("infiltrado", None)))
    opciones.append(("Salir", ("salir", None)))
    cuerpo = lineas_estado(juego)
    if juego.mision is not None and juego.mision.activa and juego.mision.objetivo():
        cuerpo += ["", "Ahora: " + juego.mision.objetivo()]
    return {"tipo": "opciones", "accion": "ayuda_menu", "zona": zona,
            "titulo": "NEXUS · Central de ayuda", "cuerpo": cuerpo,
            "opciones": [{"texto": t} for t, _ in opciones],
            "acciones": [a for _, a in opciones], "pie": _pie(jugador)}


def _panel_tema(jugador, titulo, parrafos, zona):
    cuerpo = []
    for p in parrafos:
        cuerpo += [p, ""]
    return {"tipo": "opciones", "accion": "ayuda_tema", "zona": zona,
            "titulo": titulo, "cuerpo": cuerpo[:-1],
            "opciones": [{"texto": "Volver"}], "pie": _pie(jugador)}


def confirmar_ayuda(juego, jugador):
    from data.nexus import AYUDA_TEMAS
    from juego.tutorial import pasos_con_teclas, con_teclas
    panel = jugador.panel
    zona = panel.get("zona")
    if panel["accion"] == "ayuda_tema":
        jugador.abrir_panel(panel_ayuda(juego, jugador, zona))
        return
    tipo, dato = panel["acciones"][jugador.cursor % len(panel["acciones"])]
    if tipo == "tema":
        titulo, parrafos = AYUDA_TEMAS[dato]
        jugador.abrir_panel(_panel_tema(jugador, titulo,
                                        [con_teclas(p, jugador) for p in parrafos], zona))
    elif tipo == "tutorial":
        pasos = [f"{i}. {t}" for i, t in enumerate(pasos_con_teclas(jugador), start=1)]
        jugador.abrir_panel(_panel_tema(jugador, "Tutorial", pasos, zona))
    elif tipo == "infiltrado":
        jugador.abrir_panel(juego.infiltrado.panel_terminal(jugador, zona))
    else:
        jugador.cerrar_panel()
