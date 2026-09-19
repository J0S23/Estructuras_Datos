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
| Arbol binario de busqueda (ABB) | `Estructuras/abb_publicaciones.py` | Ordena las publicaciones por su indice de veracidad. Recorrido inorden, eliminacion por sucesor inorden y busqueda por rango con poda. Sin rebalanceo. |
| Arbol N-ario de decision | `Estructuras/arbol_decision.py` | Modela publicacion -> opcion -> consecuencia, con los efectos sobre los indicadores en las hojas. |
| Arbol N-ario de dialogo | `Estructuras/arbol_dialogo.py` | Conversaciones con NPCs donde el jugador elige la rama por la que desciende. |
| Grafos | *segunda entrega* | Red social para propagar publicaciones y grafo de la ciudad para moverse entre zonas. |

## Como correrlo

Requiere Python 3 y Pygame (`pip install pygame`).

```bash
python main.py              # prototipo de mundo: mapa, personajes, pantalla dividida
python main_estructuras.py  # prototipo de logica: ABB, arboles de decision y dialogo
```

Los dos prototipos se fusionan mas adelante. Ademas hay editores para preparar
los assets:

```bash
python Editores/hitbox_editor.py     # dibujar las hitboxes de un mapa
python Editores/personaje_editor.py  # calibrar escala e hitbox de un personaje
python Editores/visor_personajes.py  # revisar que sprites y config tiene cada personaje
```

## Estructura del repositorio

- `Estructuras/` -- los arboles y sus nodos.
- `Movimiento/` -- carga de sprites, animaciones y movimiento de personajes.
- `screens/` -- las pantallas del juego (partida, ciudad, publicacion, dialogo, ayuda).
- `Editores/` -- herramientas para hitboxes y calibracion de personajes.
- `Imagenes/` -- assets (`Fondos/`, `Personajes/<nombre>/`).
- `Hitboxes/` -- los JSON que generan los editores.
- `data/` -- publicaciones y dialogos de ejemplo.