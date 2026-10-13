"""El árbol de logros de una partida (Estructuras/arbol_logros.py).

Cada logro: clave, nombre, descripcion y sus hijos (los que se abren cuando
se consigue). "rama" se hereda hacia abajo y decide el color. Se pueden
cambiar nombres y descripciones sin tocar código; si se agrega un logro nuevo,
hay que avisarle al juego cuándo se consigue (logros.py).
"""


def L(clave, nombre, descripcion, *hijos, rama=None):
    d = {"clave": clave, "nombre": nombre, "descripcion": descripcion, "hijos": list(hijos)}
    if rama:
        d["rama"] = rama
    return d


ARBOL_LOGROS = L(
    "despertar", "Despertar", "Terminar el tutorial. Los aliens también despiertan.",

    L("pasos_de_gato", "Pasos de gato", "Caminar 30 segundos en sigilo.",
      L("fantasma", "Fantasma", "Que un alien revise tu escondite y no te encuentre.",
        L("sombra", "Sombra", "Terminar una fase de la misión sin que atrapen a nadie.",
          L("nadie_me_vio", "Nadie me vio", "Escapar sin que atrapen a nadie en toda la partida."))),
      L("shhh", "Shhh", "Pasar a menos de 100 px del Ciego, en sigilo, sin que te oiga."),
      rama="sigilo"),

    L("codigo_roto", "Código roto", "Abrir la puerta de la prisión.",
      L("a_la_primera", "A la primera", "Abrirla sin fallar el código ni una vez."),
      L("sin_rumbo", "Sin rumbo", "Apagar todas las consolas de navegación.",
        L("chatarrero", "Chatarrero", "Llevar las 3 piezas a la cápsula.",
          L("libertad", "Libertad", "Escapar de la nave.",
            L("todos_a_bordo", "Todos a bordo", "Escapar sin que eliminen a nadie.")))),
      rama="escape"),

    L("conectado", "Conectado", "Entrar a NEXUS desde una terminal.",
      L("algo_no_cuadra", "Algo no cuadra", "Encontrar una prueba del infiltrado.",
        L("evidencia", "Evidencia", "Subir una prueba a NEXUS.",
          L("caso_cerrado", "Caso cerrado", "Exponer al infiltrado con las 3 pruebas."),
          L("corazonada", "Corazonada", "Acusar al infiltrado correcto antes de tener las 3 pruebas."),
          L("acusacion_falsa", "Acusación falsa", "Acusar a un inocente. La nave te delató."))),
      rama="nexus"),

    L("nadie_atras", "Nadie se queda atrás", "Sacar a un compañero de una celda.",
      L("segunda_oportunidad", "Segunda oportunidad", "Rescatar a alguien que estaba en su última vida."),
      L("medico", "Médico de guerra", "Devolverle una vida a un compañero (Regeneración)."),
      rama="equipo"),

    L("hagase_la_luz", "Hágase la luz", "Encender la caja de fusibles en un apagón.",
      L("electricista", "Electricista", "Devolver la luz en menos de 30 segundos."),
      L("trabajo_en_equipo", "Trabajo en equipo", "Abrir una puerta para dos."),
      rama="nave"),

    L("conoce_a_tu_enemigo", "Conoce a tu enemigo", "Ver de cerca a los 3 tipos de alien.",
      L("agotalo", "Agótalo", "Que el Cazador se canse persiguiéndote."),
      L("apagado", "Fuera de servicio", "Apagar a un alien con un hackeo (Tecnomante)."),
      L("por_aqui_no", "Por aquí no", "Que un sello frene a un alien (Forjador)."),
      L("titiritero", "Titiritero", "Atraer a un alien con una señal falsa (Resonante)."),
      rama="aliens"),
    rama="inicio",
)

# Colores de cada rama (cajas del árbol y del aviso).
COLOR_RAMA = {
    "inicio": (240, 242, 252),
    "sigilo": (140, 170, 255),
    "escape": (90, 220, 230),
    "nexus": (233, 120, 200),
    "equipo": (120, 230, 150),
    "nave": (255, 214, 64),
    "aliens": (245, 130, 120),
}
