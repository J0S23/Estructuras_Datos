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
]

# Publicaciones de relleno de los prisioneros: ciertas e inofensivas. Hacen que
# el feed se sienta como una red social de verdad. Compartirlas suma poquito.
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
TICK_PROPAGACION_MS = 1300      # cada cuánto avanza un nivel una publicación
PRIMER_RUMOR_S = 30             # después del tutorial
RUMOR_CADA_S = (38, 55)         # entre un rumor y el siguiente (al azar)
NORMAL_CADA_S = (14, 24)        # publicaciones de relleno
NUEVO_BOT_CADA_S = 75           # el Cambiaformas abre otra cuenta si le borraron
MAX_POR_VERIFICAR = 3           # rumores + pedidos de ayuda por ir a ver, a la vez, POR JUGADOR

# Al que le llega un rumor se lo cree con esta probabilidad, y solo si se lo
# cree lo reenvía (se pone rojo). Con la verdad pasa igual: al que le llega un
# desmentido lo convence con PROB_CONVENCER (verde) y entonces lo reenvía.
PROB_CREER_RUMOR = 0.45
PROB_CONVENCER = 0.6
PROB_CONVENCER_UBICACION = 0.8  # la foto sin recortar convence más...
                                # ...pero el alien más cercano va por ti

NIVELES_DESMENTIDO = 6          # hasta cuántos saltos puede llegar un desmentido
NIVELES_COMPARTIR_CIERTO = 1

UMBRAL_PLANOS = 0.80            # % de prisioneros verdes para los planos

# Mientras el rojo le va ganando al verde, los aliens se potencian. Con el rojo
# DIFERENCIA_POTENCIA_MAX por encima del verde llegan al máximo.
DIFERENCIA_POTENCIA_MAX = 0.5
POTENCIA_VELOCIDAD = 0.30       # +30% de velocidad al máximo
POTENCIA_VISION = 0.35          # +35% de alcance de visión al máximo

RADIO_FOTO = 70                 # qué tan cerca del lugar hay que estar

# -- Rumores que se vuelven virales ------------------------------------------------
# La desinformación no se queda en la pantalla: si nadie desmiente un rumor en
# VIRAL_S segundos (× "viral_cada" de la dificultad), se vuelve viral. A los
# grises les llega a todos y se lo creen con PROB_CREER_VIRAL, y la gente de la
# nave actúa como si fuera verdad ("viral" de cada rumor; los que no traen,
# solo se riegan). Al desmentirlo, la gente vuelve a lo de antes.
VIRAL_S = 90
PROB_CREER_VIRAL = 0.5
VIRAL_GENERICO = "Ya casi toda la nave se lo cree."
ESCONDITES_VIRAL = 3            # casilleros que ocupan los prisioneros (rumor de casilleros)
FUGA_VIRAL = 0.5                # rumor de las celdas: la fuga avanza a esta velocidad

# Llegar tarde convence menos: con la barra de "se vuelve viral" por encima de
# TARDE_DESDE, el desmentido convence cada vez menos, hasta CONVENCE_TARDE (la
# fracción de lo normal) cuando ya se volvió viral. "La mentira da la vuelta al
# mundo antes de que la verdad se ponga los zapatos."
TARDE_DESDE = 0.3
CONVENCE_TARDE = 0.5

# Las cuentas falsas que nadie reporta crecen: cada bot gana un seguidor cada
# BOT_GANA_SEGUIDOR_S segundos (× "bot_crece_cada" de la dificultad), hasta
# BOT_MAX_SEGUIDORES. Prefiere a amigos de sus seguidores (como cuando alguien
# ve que un conocido sigue una cuenta). Con más seguidores, cada rumor que
# publica les llega de una vez a más prisioneros. Reportarlo temprano corta
# una cuenta chica; tarde, una que ya le llegaba a media nave.
BOT_GANA_SEGUIDOR_S = 30
BOT_MAX_SEGUIDORES = 10
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
