"""El modo Feria (juego/feria.py): Menú > Opciones > "Modo feria".

La profe: "en la feria se tiene que poder jugar y entender en máximo 7
minutos mientras ustedes cuentan la historia". Con el modo feria prendido, la
partida (en la dificultad que se escoja) recorta lo de la misión que es largo
o que cuesta explicar, tiene reloj, el equipo se anota en el ranking al
terminar y, con el menú quieto, el juego se juega solo (juego/demo.py).
"""

FERIA = {
    "solo_primera_puerta": True,    # de las puertas con código, solo la de la salida (las otras, abiertas)
    # Cuántas consolas de navegación hay que apagar, según cuántos juegan (las
    # más cercanas caminando; Diego, nov 21: "con 2 jugadores una consola, con
    # 3 dos y con 4 tres"; antes una siempre).
    "consolas": {2: 1, 3: 2, 4: 3},
    "piezas": 3,                    # las que pide la cápsula (nov 22, Diego: de 2 a 3, como el juego normal)
    # El Guardia de la Bahía con la planta y su fruta, y las puertas para dos
    # (cada uno en un panel): van, como en el juego normal (Diego, nov 21: "que
    # vuelvan"; hasta entonces se quitaban). True los quita.
    "sin_guardia": False,
    "sin_puertas_dobles": False,
    # El caso del Cambiaformas (las 3 pruebas, subirlas y acusar): Diego, nov
    # 22: "que vuelva todo el caso, igual no es necesario completarlo para
    # ganar, pero ahí está" (hasta entonces se quitaba; True lo quita).
    "sin_caso": False,
    # El minijuego del casillero (cuando un alien lo revisa;
    # entidades/minijuego_latidos.py): Diego, nov 22: "que sea más rápido:
    # que al acertar la barra del alien baje más o que suba más lento". Las
    # dos: sube 5 por segundo (normal 7) y cada acierto la baja 22 (normal
    # 14). Simulado (300 intentos, un jugador que apunta al centro de la
    # franja con 60-110 ms de error): de ~15-21 s a ~4.5-5 s; se sigue
    # perdiendo si se falla mucho (cada fallo la sube 7, igual que antes).
    "escondite": {"sube_por_s": 5.0, "por_acierto": 22.0},
    "primer_rumor_s": 20,           # el primer rumor de NEXUS (si no, data/nexus.PRIMER_RUMOR_S)
    # Los planos: NEXUS es el centro del juego. Con un desmentido la verdad
    # llegaba a casi todos (~90 %) y bastaban 1 o 2 para los planos, así que
    # subir el % solo no servía: cada prisionero al que le llega la verdad se
    # convence con menos probabilidad ("convencer", abajo y en
    # data/dificultad.AJUSTES; los que no, la frenan y el siguiente desmentido
    # vuelve a intentar con ellos) y en la feria se pide al menos el 70 %.
    # Hacen falta unos 2 desmentidos o confirmaciones con el 70 % (medido:
    # pruebas/prueba_feria.py, sección 6).
    # Nov 21, Diego: "que la confianza suba más rápido, ahora sube muy lento":
    # la verdad avanza un nivel cada `tick_verde_ms` (0.6 s; en el juego normal
    # data/nexus.TICK_PROPAGACION_MS, 1.8 s), convence más ("convencer" 0.65,
    # antes 0.5) y, para que los planos no salgan con uno o dos, piden el 80 %.
    # Simulado (8 semillas, un rumor por minuto desmentido a los 35 s): verde
    # al minuto 1 / 2 / 3, 14 / 35 / 57 % -> 46 / 74 / 85 %; los planos, con 3
    # desmentidos (mediana; antes 4-5) a los ~3 minutos (antes ~4-5).
    # Nov 24, Diego: "baja un poquito el nivel de confianza necesario": 80 -> 70 %.
    "umbral_planos_min": 0.70,      # % de verdes para los planos (si la dificultad pide más, lo de ella)
    "tick_verde_ms": 600,           # cada cuánto avanza un nivel la verdad (desmentidos y confirmaciones)
    "limite_s": 12 * 60,            # (Diego, nov 21: 12 min; antes 9) se acaba el tiempo -> termina la partida (None = sin reloj)
    "avisos_s": (120, 60),          # "Nos quedan 2 minutos", "1 minuto"
}
# Lo de data/dificultad.AJUSTES que en el modo feria va distinto (en cualquier dificultad).
AJUSTES_FERIA = {
    "rumor_cada": 0.85,             # un rumor más seguido (para que se use NEXUS en 7 minutos)
    "bot_crece_cada": 100.0,        # las cuentas falsas no ganan seguidores (no da tiempo de explicarlo)
    # Cuánto convence la verdad, por dificultad (Fácil, Normal, Difícil,
    # Pesadilla; ver arriba). Antes 0.65 en todas: con el 70 % hacían falta
    # ~4-5 misiones (Joseph, nov 25). Ahora, medido como en data/dificultad.py:
    # mediana de 2 en Fácil y Normal, y 2-3 en Difícil.
    "convencer": [0.85, 0.78, 0.68, 0.62],
}
