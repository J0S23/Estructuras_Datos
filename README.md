# Alcalde Digital

Videojuego educativo en Python/Pygame sobre el uso responsable de las redes
sociales. Proyecto de laboratorio de **Estructura de Datos II**, Universidad
del Norte.

Ciudad Nova esta en elecciones. Los ciudadanos se comunican por una red social
ficticia llamada **Civitas**, donde circulan rumores y noticias falsas. Los
jugadores deciden que hacer con cada publicacion --verificar, compartir,
ignorar o reportar-- y cada decision mueve los indicadores de la ciudad:
informacion verificada, confianza ciudadana, convivencia, bienestar digital,
desinformacion y conflictos. No hay preguntas de conocimiento: se aprende por
las consecuencias.

## Estructuras de datos

| Estructura | Donde | Para que |
|---|---|---|
| Arbol binario de busqueda (ABB) | `Estructuras/abb_publicaciones.py` | Ordena las publicaciones por su indice de veracidad. Insertar, buscar, eliminar por sucesor inorden, recorrido inorden, busqueda por rango con poda, altura y conteo. Sin rebalanceo. Se puede ver dibujado con [A]. |
| Arbol N-ario de decision | `Estructuras/arbol_decision.py` | Modela publicacion -> opcion -> consecuencia, con los efectos sobre los indicadores en las hojas. |
| Arbol N-ario de dialogo | `Estructuras/arbol_dialogo.py` | Conversaciones con NPCs donde el jugador elige la rama por la que desciende. |
| Arbol binario de habilidades | `Estructuras/arbol_habilidades.py` | Progresion de cada rol durante la ronda. Al subir se escoge **una de dos** ramas y la otra se cierra, asi que lo desbloqueado cambia las opciones que el jugador ve. Recorrido por niveles (BFS) para dibujarlo y preorden para descartar la rama perdida. |
| Grafos | *segunda entrega* | Red social para propagar publicaciones y grafo de la ciudad para moverse entre zonas. |

## Como correrlo

Requiere Python 3 y Pygame (`pip install pygame`).

```bash
python main.py                        # el juego
python pruebas/prueba_partida.py      # una ronda completa sin abrir ventana
python pruebas/prueba_seleccion.py    # el flujo de cantidad y roles, a 2, 3 y 4
python pruebas/prueba_controles.py    # que nadie se robe las teclas de otro
python pruebas/prueba_paneles.py      # los paneles a varias resoluciones
python pruebas/prueba_estructuras.py  # los arboles por consola
python pruebas/prueba_textos.py       # que la fuente pueda dibujar todo el texto
```

### Como se juega

Al darle **Jugar** se pregunta primero cuantos juegan (2, 3 o 4) y despues cada
uno escoge su rol desde su propia seccion de pantalla. Dos jugadores no pueden
quedarse con el mismo rol. Ya en partida, cada uno camina hasta las zonas
marcadas en su trozo de pantalla y presiona su tecla de interaccion.

| | Jugador 1 | Jugador 2 | Jugador 3 | Jugador 4 |
|---|---|---|---|---|
| Moverse | WASD | Flechas | *pendiente de mando* | *pendiente de mando* |
| Interactuar / confirmar | E | Enter | O | Y |
| Elegir opcion | W / S | Flecha arriba / abajo | I / K | T / G |
| Arbol de habilidades | Q | Shift derecho | U | R |

Los jugadores 3 y 4 llevan teclas **provisionales**: sirven para escoger rol,
pero en partida todavia no se mueven porque les toca mando y eso no esta hecho.
Se ven en el mapa igual. Todos se mueven a la misma velocidad: no hay tecla de
correr.

Teclas globales: **[TAB]** dibuja el ABB de publicaciones tal como esta en
memoria, **[H]** muestra las hitboxes, **[F11]** alterna ventana, **[ESC]**
vuelve al menu. La ronda dura cinco minutos y termina en una pantalla de
resultados.

Las zonas del mapa: el **Tablon**, la **Junta de vecinos** y la **Casa de un
vecino** son del ciudadano (verificar publicaciones, reportar las falsas y
hablar con un vecino); la **Plaza** y la **Emisora** son del candidato
(responder acusaciones y presentar propuestas). Ademas hay editores para preparar
los assets:

```bash
python Editores/hitbox_editor.py     # dibujar las hitboxes de un mapa
python Editores/personaje_editor.py  # calibrar escala e hitbox de un personaje
python Editores/visor_personajes.py  # revisar que sprites y config tiene cada personaje
```

## Estructura del repositorio

- `Estructuras/` -- los arboles y sus nodos.
- `jugador.py` -- un jugador: su personaje, rol, puntos y arbol de habilidades.
- `pruebas/` -- pruebas que corren sin abrir ventana.

Los personajes dibujados hasta ahora son **Anny** y **Joseph**
(`Imagenes/Personajes/<Nombre>/<Nombre>_<animacion>_<direccion>.png`). Con 3 o
4 jugadores se repiten hasta que haya arte para los que faltan.
- `Movimiento/` -- carga de sprites, animaciones y movimiento de personajes.
- `screens/` -- las pantallas del juego (partida, ciudad, publicacion, dialogo, ayuda).
- `Editores/` -- herramientas para hitboxes y calibracion de personajes.
- `Imagenes/` -- assets (`Fondos/`, `Personajes/<nombre>/`).
- `Hitboxes/` -- los JSON que generan los editores.
- `data/` -- publicaciones y dialogos de ejemplo.