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
| Moverse | WASD | Flechas | mando: stick o cruceta | mando: stick o cruceta |
| Interactuar / confirmar | E | Enter | A (o O) | A (o Y) |
| Elegir opcion | W / S | Flecha arriba / abajo | stick / cruceta (o I / K) | stick / cruceta (o T / G) |
| Arbol de habilidades | Q | Shift derecho | Y (o U) | Y (o R) |
| Usar habilidad | F | - (junto al Shift derecho) | X (o P) | X (o V) |
| Caminar en sigilo (mantener) | Shift izquierdo | AltGr o 0 del numerico | LB o LT | LB o LT |
| Cerrar un panel | - | - | B | B |

Los jugadores 3 y 4 juegan con mando (Xbox o parecido): el primero que se
conecta es del jugador 3 y el segundo del 4. Sin mando escogen rol con las
letras del teclado pero en partida no se mueven. En los menus el mando hace de
flechas y Enter. `python pruebas/probar_mando.py` muestra que boton manda cada
cosa por si algun mando sale con los numeros cambiados (se ajusta en `mandos.py`). No hay tecla de correr; la de sigilo hace caminar a la
mitad de velocidad y casi sin ruido.

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
python Editores/editor_mapa.py       # poner aliens, escondites, terminales... (ver abajo)
python Editores/hitbox_editor.py     # dibujar las hitboxes de un mapa
python Editores/personaje_editor.py  # calibrar escala e hitbox de un personaje
python Editores/visor_personajes.py  # revisar que sprites y config tiene cada personaje
```

### La mision (mapa de la nave)

Cuatro prisioneros escapan de una nave alienigena en tres fases: abrir la
puerta de la prision con el codigo que esta en una de las notas, apagar las
consolas de navegacion y reparar la capsula de escape; despues los aliens
entran en alerta y todos tienen que llegar a la capsula. Si atrapan a alguien
va a una celda y otro lo tiene que sacar. Las consolas y la reparacion se hacen
**manteniendo** la tecla de interactuar. La habilidad escogida se usa con **F**
(jugador 1) o **-** (jugador 2, la tecla junto al Shift derecho) y se paga con puntos del equipo.

La nave esta iluminada, pero si sale el evento de **apagon** todo queda a
oscuras (cada uno ve lo que alumbra su linterna, y de los aliens fuera de la
luz solo se ven los ojos) hasta que alguien encuentre la caja de fusibles que
parpadea en rojo y la encienda manteniendo la tecla. Hay cuatro tipos de alien
(Rastreador, Vigia, Ciego y Cazador) con el mismo arbol de comportamiento y
distintos sentidos. Cada minuto, mas o menos, la nave lanza un evento al azar
(apagon, alarma o cierre de una compuerta; solo puede haber un apagon a la vez), y la puerta a la sala de control se
abre solo con dos jugadores, cada uno en un panel. La partida empieza con un
tutorial de 30 segundos mientras los aliens duermen. **[L]** apaga la oscuridad.

```bash
python pruebas/prueba_mision.py    # juega la mision completa sin ventana
python pruebas/prueba_sorpresas.py # oscuridad, aliens, sigilo, eventos, puertas, tutorial
python pruebas/simulador.py 8      # bots que juegan 8 partidas: bugs y balance
python pruebas/prueba_hud.py       # capturas del HUD con 2, 3 y 4 jugadores
```

### Editar el mapa sin tocar codigo

`python Editores/editor_mapa.py` abre el mapa y deja poner con el mouse todo lo
que va encima: inicio de los jugadores, rutas de los aliens, escondites,
celdas, puerta de la prision, notas, consolas, capsula, piezas, terminales NEXUS,
terminales y paneles de los roles, consumibles y zonas (la lista con sus teclas
esta en el editor). Clic izquierdo pone o arrastra, clic derecho borra, `Ctrl+S` guarda,
`M` hace que el juego use ese mapa y `F5` guarda y abre el juego para probar.
Marca en rojo lo que choca con paredes y en naranja lo que no se alcanza
caminando. Guarda en `Hitboxes/<mapa>_objetos.json`; las paredes se siguen
dibujando con `hitbox_editor.py`. Para un mapa nuevo: dibujar sus paredes con
el editor de hitboxes y despues poner todo lo demas con el editor de mapa.

```bash
python pruebas/prueba_editor_mapa.py  # el editor y que el juego use lo guardado
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