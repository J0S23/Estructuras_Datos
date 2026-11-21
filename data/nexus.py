"""Datos de NEXUS, la red social de la nave (nexus.py). Se pueden editar sin
tocar código: nombres de las cuentas, rumores, textos y números del balance.

Cómo funciona, en corto:
- Cada cuenta es un nodo del grafo (Estructuras/grafo.py). Cada prisionero
  sigue a unos cuantos; lo que alguien publica les llega a sus seguidores, y
  si lo comparten, a los seguidores de ellos (BFS, un nivel por tick).
- Cada prisionero (CUENTAS) puede estar gris (no decide), verde (confía en
  los jugadores) o rojo (le cree a los aliens). Las barras de confianza son el
  % de prisioneros verdes y rojos.
- Los BOTS parecen prisioneros, pero son cuentas del Cambiaformas: publican
  RUMORES falsos. Cada rumor habla de un lugar de la nave; para desmentirlo hay
  que ir a ese lugar, sacar una foto y publicarla.
"""

# -- Cuentas -----------------------------------------------------------------------
# "usuario" es lo que se ve en el celular. Pueden agregar o quitar cuentas:
# el grafo se arma solo con las que haya.
# "sprites": qué carpetas de Imagenes/Prisioneros/ le quedan bien a esa persona
# (la primera que no esté usada en la partida; si ya están todas, la menos
# usada). Sin "sprites", o si no existe ninguna, le toca cualquiera.
#   NPC_1 joven de pelo corto       NPC_2 señor mayor, canoso
#   NPC_3 joven de pelo castaño     NPC_4 joven con la venda en el ojo
#   NPC_5 señora mayor, canosa      NPC_6 niño con el brazo en cabestrillo
#   NPC_7 joven de pelo afro        NPC_8 joven de pelo largo y claro
CUENTAS = [
    {"nombre": "Dra. Vega", "usuario": "@dra_vega", "sprites": ["NPC_7", "NPC_3", "NPC_8"]},
    {"nombre": "Mecánico Ruiz", "usuario": "@ruiz_llaves", "sprites": ["NPC_4", "NPC_1"]},
    {"nombre": "Lía, la piloto", "usuario": "@lia_vuela", "sprites": ["NPC_3", "NPC_8", "NPC_7"]},
    {"nombre": "Cabo Duarte", "usuario": "@cabo_duarte", "sprites": ["NPC_1", "NPC_4"]},
    {"nombre": "El Profe", "usuario": "@elprofe", "sprites": ["NPC_2"]},
    {"nombre": "Nadia (cocina)", "usuario": "@nadia_cocina", "sprites": ["NPC_7", "NPC_8", "NPC_3"]},
    {"nombre": "Tomás", "usuario": "@tomas_17", "sprites": ["NPC_6", "NPC_1", "NPC_4"]},
    {"nombre": "Sofi", "usuario": "@sofi.estrellas", "sprites": ["NPC_8", "NPC_3", "NPC_7"]},
    {"nombre": "Don Hernán", "usuario": "@don_hernan", "sprites": ["NPC_2"]},
    {"nombre": "Mariana", "usuario": "@mari_ana", "sprites": ["NPC_7", "NPC_8", "NPC_3"]},
    {"nombre": "Kevin", "usuario": "@kevin_gamer", "sprites": ["NPC_6", "NPC_4", "NPC_1"]},
    {"nombre": "Abuela Rosa", "usuario": "@abuela_rosa", "sprites": ["NPC_5"]},
    {"nombre": "Julián", "usuario": "@julian_foto", "sprites": ["NPC_1", "NPC_4"]},
    {"nombre": "Valen", "usuario": "@valen.v", "sprites": ["NPC_8", "NPC_3", "NPC_7"]},
]

# Cuentas falsas del Cambiaformas: se ven como prisioneros cualquiera, con
# la foto de alguien de verdad ("sprites": la foto de perfil que usan, como
# las de CUENTAS; Imagenes/Perfiles/).
BOTS = [
    {"nombre": "Prisionero 47", "usuario": "@p47_libre", "sprites": ["NPC_6"]},
    {"nombre": "Ana Verdad", "usuario": "@la_verdad_ana", "sprites": ["NPC_7"]},
    {"nombre": "Info Nave 24/7", "usuario": "@infonave247", "sprites": ["NPC_1"]},
    {"nombre": "Camila", "usuario": "@cami_real", "sprites": ["NPC_8"]},
    {"nombre": "Noticias Ya", "usuario": "@noticias_ya", "sprites": ["NPC_4"]},
]

# Cuántas cuentas (al azar) recibe lo que publica cada uno.
SEGUIDORES_PRISIONERO = 2
SEGUIDORES_BOT = 3                 # los bots tienen más alcance
SEGUIDORES_JUGADOR = 3
# A cada jugador le llega lo que publican tantas cuentas (su feed).
SIGUE_CADA_JUGADOR = 4
BOTS_AL_EMPEZAR = 3

# -- Rumores --------------------------------------------------------------------------
# "lugar" dice dónde se verifica: capsula, consola, celda, fusibles, escondite,
# terminal, panel o puerta_doble (lo que exista en el mapa). "foto" es lo que se
# ve al llegar; "desmentido" es lo que se publica con la foto. "viral" es lo
# que pasa en la nave si nadie lo desmiente a tiempo (ver VIRAL_S abajo).
RUMORES = [
    {"lugar": "capsula",
     "texto": "Se los juro: la cápsula de escape explotó. No hay salida, mejor ríndanse.",
     "foto": "La cápsula está entera. Solo le faltan piezas.",
     "desmentido": "Fui a la cápsula: está entera. NO explotó. Foto aquí.",
     "viral": "Los prisioneros se rindieron: ya nadie quiere ir a la cápsula contigo."},
    {"lugar": "consola",
     "texto": "Las consolas de navegación dan una descarga mortal si las tocas. No se acerquen.",
     "foto": "La consola funciona normal. No hay ninguna trampa.",
     "desmentido": "Toqué la consola de navegación y no pasó nada. Es falso lo de la descarga."},
    {"lugar": "celda",
     "texto": "Las celdas tienen gas venenoso. Si alguien cae preso, no vayan a rescatarlo.",
     "foto": "Las celdas están limpias. No hay ningún gas.",
     "desmentido": "Estuve en las celdas: no hay gas. Si atrapan a alguien, ¡vayan por él!",
     "viral": "Nadie se acerca a las celdas: el que caiga preso tarda el doble en forzar la reja."},
    {"lugar": "fusibles",
     "texto": "Si tocas una caja de fusibles la nave se autodestruye. No las toquen nunca.",
     "foto": "Es una caja de fusibles normal, nada de autodestrucción.",
     "desmentido": "Revisé la caja de fusibles: es una caja normal. Nada de autodestrucción."},
    {"lugar": "escondite",
     "texto": "Los aliens sellaron todos los casilleros. Ya no hay dónde esconderse.",
     "foto": "El casillero abre bien. Se puede usar.",
     "desmentido": "Abrí un casillero hace un momento: no están sellados. Foto de prueba.",
     "viral": "Los prisioneros corrieron a meterse en los casilleros que quedan: hay menos escondites para ustedes."},
    {"lugar": "terminal",
     "texto": "Las terminales graban tu cara y se la mandan a los aliens. No las usen.",
     "foto": "La terminal no tiene cámara. Solo muestra el mapa de la nave.",
     "desmentido": "Las terminales no tienen cámara, miren. Ese rumor es falso.",
     "viral": "Los prisioneros desconectaron una terminal NEXUS por miedo: quedó fuera de servicio."},
    {"lugar": "panel",
     "texto": "Los paneles de reparación están rotos para siempre. Los aliens ganaron.",
     "foto": "El panel se puede reparar con piezas.",
     "desmentido": "Los paneles se pueden reparar, lo comprobé. No les crean a los aliens."},
    {"lugar": "puerta_doble",
     "texto": "La puerta del pasillo de control está soldada. Ni lo intenten.",
     "foto": "La puerta no está soldada: se abre con dos personas.",
     "desmentido": "La puerta del pasillo NO está soldada: se abre entre dos. Foto."},
    # Rumores que suenan a noticia de verdad (cosas chicas y concretas, como
    # las de NOTICIAS): por cómo suena ya no se sabe si es falso; hay que ir a
    # ver o fijarse en quién lo publicó (Diego, nov 20).
    {"lugar": "capsula",
     "texto": "Anoche le sacaron el motor a la cápsula de escape, la vi vacía por dentro.",
     "foto": "El motor sigue en la cápsula. Solo le faltan piezas.",
     "desmentido": "Fui a la cápsula: el motor está en su lugar. Nadie se lo llevó.",
     "viral": "Los prisioneros se rindieron: ya nadie quiere ir a la cápsula contigo."},
    {"lugar": "consola",
     "texto": "Ya alguien apagó las consolas de navegación del otro lado. No hace falta ir.",
     "foto": "La consola sigue prendida: nadie la ha apagado.",
     "desmentido": "Las consolas siguen prendidas, nadie las apagó. Hay que ir a apagarlas."},
    {"lugar": "celda",
     "texto": "Le cambiaron la cerradura a las celdas: ya no se abren desde afuera.",
     "foto": "La reja abre normal desde afuera.",
     "desmentido": "Las celdas se abren normal desde afuera. Si encierran a alguien, se le puede sacar.",
     "viral": "Nadie se acerca a las celdas: el que caiga preso tarda el doble en forzar la reja."},
    {"lugar": "fusibles",
     "texto": "La caja de fusibles de este pasillo tiene los breakers botados, por eso falla la luz.",
     "foto": "Los breakers están todos arriba. La caja está bien.",
     "desmentido": "Revisé la caja de fusibles: los breakers están arriba. No le pasa nada."},
    {"lugar": "escondite",
     "texto": "Un casillero quedó con la puerta trabada, ya no abre.",
     "foto": "El casillero abre bien. Se puede usar.",
     "desmentido": "Probé el casillero: abre perfecto, no está trabado.",
     "viral": "Los prisioneros corrieron a meterse en los casilleros que quedan: hay menos escondites para ustedes."},
    {"lugar": "terminal",
     "texto": "Una terminal se quedó colgada mostrando ruido. Mejor ni la toquen.",
     "foto": "La terminal responde normal.",
     "desmentido": "La terminal funciona bien, no estaba colgada.",
     "viral": "Los prisioneros desconectaron una terminal NEXUS por miedo: quedó fuera de servicio."},
    {"lugar": "panel",
     "texto": "Un panel de reparación se quedó sin corriente. Ya no sirve aunque le pongan piezas.",
     "foto": "El panel tiene corriente. Se puede reparar con piezas.",
     "desmentido": "El panel tiene corriente: con una pieza se repara. Era mentira."},
    {"lugar": "puerta_doble",
     "texto": "El lector de la puerta para dos está desconectado, por más que lo intenten no abre.",
     "foto": "El lector tiene luz y responde: se abre entre dos.",
     "desmentido": "El lector de la puerta funciona: entre dos se abre. Foto."},
]

# -- Noticias verdaderas --------------------------------------------------------------
# Las publica un prisionero de verdad (no un bot) y lo que cuentan ES cierto:
# en Misiones se ven igual que los rumores (no se sabe cuál es cuál hasta ir a
# ver). Verificarla es ir al lugar y ARREGLARLO con un minijuego (`arreglo`,
# misiones/minijuegos.py; sin minijuegos, se arregla solo al llegar). Con la foto se
# publica `confirmacion`. "efecto" = lo que pasa en la nave mientras nadie lo
# arregla ("candado": ese casillero no se puede usar). "viral" es lo que se
# avisa si se riega por toda la nave antes de que alguien la verifique, y
# "empeora", lo que pasa entonces si nadie lo arregló (Diego, nov 21: que lo
# verdadero también tenga consecuencias; redes/nexus._empeorar): los breakers
# terminan en un apagón, el panel en corto baja una compuerta, la terminal se
# desconecta, las celdas cuestan el doble y la puerta para dos se queda sin
# corriente (hasta que alguien lo arregle). Y la gente ve que nadie hace nada:
# cada verde deja de confiar con PROB_DESCONFIAR.
NOTICIAS = [
    {"lugar": "escondite",
     "texto": "Ojo: le pusieron candado a un casillero. Ya no sirve para esconderse.",
     "foto": "El casillero sí tenía candado. Ya está abierto.",
     "confirmacion": "Era cierto: un casillero tenía candado. Lo forcé y ya se puede usar.",
     "arreglo": "ganzua", "titulo_arreglo": "El casillero tiene candado: fuérzalo",
     "pista": "Revisar el casillero", "efecto": "candado",
     "viral": "Toda la nave sabe lo del candado: nadie usa ese casillero.",
     "empeora": "El casillero sigue con candado y nadie hace nada."},
    {"lugar": "fusibles",
     "texto": "La caja de fusibles de mi pasillo tiene los breakers botados. Por eso parpadea la luz.",
     "foto": "Los breakers sí estaban abajo. Ya están arriba.",
     "confirmacion": "Era cierto lo de los breakers de la caja de fusibles. Ya los subí.",
     "arreglo": "interruptores", "titulo_arreglo": "Breakers botados: sube las palancas",
     "pista": "Revisar la caja de fusibles",
     "viral": "Toda la nave sabe lo de la caja de fusibles.",
     "empeora": "Nadie subió los breakers: la caja se quemó y ¡se fue la luz de la nave!"},
    {"lugar": "panel",
     "texto": "Un panel de reparación está echando chispas: tiene los cables cruzados.",
     "foto": "Los cables del panel sí estaban cruzados. Ya están en su lugar.",
     "confirmacion": "Era cierto: el panel tenía los cables cruzados. Ya lo arreglé.",
     "arreglo": "cables", "titulo_arreglo": "Panel en corto: conecta los cables",
     "pista": "Revisar el panel",
     "viral": "Toda la nave sabe lo del panel en corto.",
     "empeora": "Nadie arregló el panel en corto: saltó el cierre de emergencia y bajó una compuerta."},
    {"lugar": "terminal",
     "texto": "Una terminal se quedó colgada mostrando puro ruido. Que alguien la reinicie.",
     "foto": "La terminal sí estaba colgada. Ya responde.",
     "confirmacion": "Era cierto: la terminal estaba colgada. La resintonicé y ya funciona.",
     "arreglo": "senal", "titulo_arreglo": "Terminal colgada: sintoniza la señal",
     "pista": "Revisar la terminal",
     "viral": "Toda la nave sabe lo de la terminal colgada.",
     "empeora": "Nadie reinició la terminal: se desconectó del todo hasta que alguien la arregle."},
    {"lugar": "celda",
     "texto": "La cerradura de una celda quedó trabada. Si encierran a alguien ahí, va a costar sacarlo.",
     "foto": "La cerradura sí estaba trabada. Ya abre bien.",
     "confirmacion": "Era cierto lo de la cerradura de la celda. La destrabé.",
     "arreglo": "ganzua", "titulo_arreglo": "Cerradura trabada: destrábala",
     "pista": "Revisar la cerradura de la celda",
     "viral": "Toda la nave sabe lo de la cerradura trabada.",
     "empeora": "Nadie destrabó la cerradura: ahora cuesta el doble salir de las celdas."},
    {"lugar": "puerta_doble",
     "texto": "El lector de la puerta del pasillo tiene los cables sueltos, se apaga a ratos.",
     "foto": "Los cables del lector sí estaban sueltos. Ya están conectados.",
     "confirmacion": "Era cierto: el lector de la puerta tenía cables sueltos. Ya los conecté.",
     "arreglo": "cables", "titulo_arreglo": "Lector de la puerta: conecta los cables",
     "pista": "Revisar el lector de la puerta",
     "viral": "Toda la nave sabe lo del lector de la puerta.",
     "empeora": "Nadie arregló el lector: la puerta para dos se quedó sin corriente hasta que alguien conecte sus cables."},
]
# Noticias verdaderas que suenan alarmantes, como los rumores (Diego: que no
# se note cuál es verdad por cómo suena). Lo demás es igual a la de su lugar.
_ALARMANTES = {
    "escondite": "¡Le pusieron candado a un casillero! ¡Ya no hay dónde meterse!",
    "fusibles": "¡La caja de fusibles está echando chispas! ¡Se va a ir la luz de toda la nave!",
    "panel": "¡Un panel explotó en el pasillo, salen chispas por todos lados!",
    "terminal": "¡Una terminal se volvió loca, solo muestra estática! ¡Algo le hicieron!",
    "celda": "¡Una celda quedó trabada! ¡Si te encierran ahí no sales nunca!",
    "puerta_doble": "¡La puerta para dos se apaga sola! ¡Nos van a dejar encerrados!",
}
NOTICIAS += [dict(n, texto=_ALARMANTES[n["lugar"]]) for n in list(NOTICIAS) if n["lugar"] in _ALARMANTES]
PROB_NOTICIA = 0.4              # de lo que va a Misiones, qué parte es verdad
PUNTOS_ARREGLAR = 10            # al arreglarlo en el lugar (antes de publicar)
PUNTOS_CONFIRMAR = 15           # al publicar la foto

# Publicaciones de relleno de los prisioneros: ciertas e inofensivas. Hacen que
# el feed se sienta como una red social de verdad. Compartirlas no da puntos ni
# cambia la confianza: no hay nada que verificar.
NORMALES = [
    "¿Alguien más tiene hambre? Llevo dos días sin comer nada decente.",
    "Extraño el sol. Aquí todo es luz azul.",
    "Hoy hice 50 flexiones en la celda. Hay que mantenerse fuerte.",
    "Si salimos de esta, prometo llamar a mi mamá todos los días.",
    "¿Alguien sabe qué día es hoy?",
    "Encontré una foto de mi perro en el bolsillo. Me dio ánimo.",
    "Respiren hondo. Asustados pensamos peor.",
    "Gracias a los que nos están ayudando a escapar.",
]

# -- Balance ------------------------------------------------------------------------
TICK_PROPAGACION_MS = 1800      # cada cuánto avanza un nivel una publicación (nov 12: antes 1300)
PRIMER_RUMOR_S = 50             # después del tutorial (antes 30)
RUMOR_CADA_S = (60, 85)         # entre un rumor y el siguiente (al azar; antes 38-55)
NORMAL_CADA_S = (14, 24)        # publicaciones de relleno
NUEVO_BOT_CADA_S = 75           # el Cambiaformas abre otra cuenta si le borraron
MAX_POR_VERIFICAR = 3           # rumores + pedidos de ayuda por ir a ver, a la vez, POR JUGADOR

# Al que le llega un rumor se lo cree con esta probabilidad, y solo si se lo
# cree lo reenvía (se pone rojo). Con la verdad pasa igual: al que le llega un
# desmentido lo convence con PROB_CONVENCER (verde) y entonces lo reenvía.
PROB_CREER_RUMOR = 0.30
PROB_CONVENCER = 0.85
PROB_CONVENCER_UBICACION = 0.95  # la foto sin recortar convence más...
                                # ...pero el alien más cercano va por ti

NIVELES_DESMENTIDO = 8          # hasta cuántos saltos puede llegar un desmentido
# Al desmentir, cada uno de los que se creyeron ESE rumor y siguen en rojo
# recapacita (vuelve a gris) con esta probabilidad (× lo de llegar tarde),
# aunque el desmentido no le llegue por la red.
PROB_RECAPACITAR = 0.6
# Y con el tiempo la gente duda: cada OLVIDO_CADA_S, cada prisionero en rojo
# vuelve a gris con PROB_OLVIDAR (así el rojo no se queda arriba para siempre).
OLVIDO_CADA_S = 20
PROB_OLVIDAR = 0.08
NIVELES_COMPARTIR_CIERTO = 1

UMBRAL_PLANOS = 0.65            # % de prisioneros verdes para los planos (sin dificultad)

# Mientras el rojo le va ganando al verde, los aliens se potencian. Con el rojo
# DIFERENCIA_POTENCIA_MAX por encima del verde llegan al máximo.
DIFERENCIA_POTENCIA_MAX = 0.7
POTENCIA_VELOCIDAD = 0.15       # +15% de velocidad al máximo (antes 30%)
POTENCIA_VISION = 0.20          # +20% de alcance de visión al máximo (antes 35%)

RADIO_FOTO = 70                 # qué tan cerca del lugar hay que estar

# -- Rumores que se vuelven virales ------------------------------------------------
# La desinformación no se queda en la pantalla: si nadie desmiente un rumor en
# VIRAL_S segundos (× "viral_cada" de la dificultad), se vuelve viral. A los
# grises les llega a todos y se lo creen con PROB_CREER_VIRAL, y la gente de la
# nave actúa como si fuera verdad ("viral" de cada rumor; los que no traen,
# solo se riegan). Al desmentirlo, la gente vuelve a lo de antes.
VIRAL_S = 150                   # (antes 90)
PROB_CREER_VIRAL = 0.3          # (antes 0.5)
VIRAL_GENERICO = "Ya casi toda la nave se lo cree."
ESCONDITES_VIRAL = 3            # casilleros que ocupan los prisioneros (rumor de casilleros)
FUGA_VIRAL = 0.5                # rumor de las celdas: la fuga avanza a esta velocidad
PROB_DESCONFIAR = 0.35          # noticia verdadera que nadie arregló a tiempo: cada verde vuelve a gris

# Llegar tarde convence menos: con la barra de "se vuelve viral" por encima de
# TARDE_DESDE, el desmentido convence cada vez menos, hasta CONVENCE_TARDE (la
# fracción de lo normal) cuando ya se volvió viral. "La mentira da la vuelta al
# mundo antes de que la verdad se ponga los zapatos."
TARDE_DESDE = 0.5
CONVENCE_TARDE = 0.7

# Las cuentas falsas que nadie reporta crecen: cada bot gana un seguidor cada
# BOT_GANA_SEGUIDOR_S segundos (× "bot_crece_cada" de la dificultad), hasta
# BOT_MAX_SEGUIDORES. Prefiere a amigos de sus seguidores (como cuando alguien
# ve que un conocido sigue una cuenta). Con más seguidores, cada rumor que
# publica les llega de una vez a más prisioneros. Reportarlo temprano corta
# una cuenta chica; tarde, una que ya le llegaba a media nave.
BOT_GANA_SEGUIDOR_S = 45          # (antes 30)
BOT_MAX_SEGUIDORES = 8             # (antes 10)
AVISOS_SEGUIDORES = (6, BOT_MAX_SEGUIDORES)   # a cuántos seguidores avisa a todos
SEGUIDORES_PARA_CONSEJO = 8     # ganados en la partida sin reportar ningún bot: consejo en resultados

PUNTOS_DESMENTIR = 15
PUNTOS_REPORTAR_BOT = 10
PUNTOS_PLANOS = 25
PUNTOS_SUPLANTACION = 15        # reportar que el Cambiaformas usa la cuenta de alguien

# Cómo se nombra cada lugar en el celular ("Habla de: ...").
NOMBRE_LUGAR = {
    "capsula": "la cápsula de escape",
    "consola": "una consola de navegación",
    "celda": "las celdas",
    "fusibles": "una caja de fusibles",
    "escondite": "un casillero",
    "terminal": "una terminal",
    "panel": "un panel de reparación",
    "puerta_doble": "la puerta del pasillo",
}

# -- Central de ayuda (Terminales NEXUS) ---------------------------------------------
# Las terminales del mapa son centrales de ayuda: muestran cómo va la confianza
# y estos temas. {celular} e {interactuar} se cambian por las teclas del jugador.
AYUDA_TEMAS = [
    ("Cómo usar el celular", [
        "Abre NEXUS con {celular}. Ahí te llega lo que publican las cuentas que sigues.",
        "Elige una publicación con {interactuar} para verla y decidir qué hacer: "
        "ir a verificarla, compartirla, reportar o ver de dónde salió.",
        "Ojo: con el celular abierto no caminas. Si un alien llega, te atrapa. "
        "Úsalo en un lugar seguro y ciérralo rápido.",
    ]),
    ("¿Cómo reconozco un rumor falso?", [
        "Desconfía de lo que da miedo o urgencia (\"¡corran!\", \"ríndanse\"), de lo que "
        "no dice de dónde salió y de lo que nadie más confirma.",
        "Antes de compartir, verifica: ve al lugar del que habla y saca una foto. "
        "Con la foto lo desmientes y la verdad corre por la red.",
        "Compartir sin verificar riega el rumor y tus seguidores dejan de creerte.",
    ]),
    ("Cuidar tu ubicación", [
        "Una foto tal cual muestra dónde estás. Convence a más gente, pero los "
        "aliens también leen NEXUS: el más cercano irá por ti.",
        "Recortar el fondo protege tu ubicación. En las redes de verdad pasa igual: "
        "piensa qué dice de ti lo que publicas.",
    ]),
    ("Cuentas falsas y reportes", [
        "El Cambiaformas abre cuentas que parecen prisioneros para regar rumores.",
        "Usa \"¿De dónde salió esto?\" para ver quién lo empezó. Reporta a esa cuenta: "
        "se borra y el rumor deja de pasar por ahí.",
        "Reportar a alguien que solo se creyó el rumor no frena nada y lo aleja de "
        "ustedes. Busquen la fuente.",
    ]),
    ("Perfiles falsos en persona", [
        "El Cambiaformas puede verse y escribir igual que un prisionero. Si alguien "
        "te cita a un lugar apartado, mira \"¿De dónde salió esto?\": si dice "
        "\"dispositivo desconocido\", es una suplantación. Repórtala.",
        "Que alguien se vea como tu amigo no prueba que lo sea. Si un prisionero no "
        "habla, se te pega demasiado o otros te preguntan \"¿por qué vas con él?\", "
        "desconfía.",
        "Muévanse en grupo: solo, el Cambiaformas se atreve; juntos, se lo piensa. "
        "En la vida real igual: si vas a ver a alguien que solo conoces por redes, "
        "que sea en un lugar público y avísale a alguien.",
    ]),
]
