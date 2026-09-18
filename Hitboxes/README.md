# Hitboxes generadas por los editores

Esta carpeta se llena automáticamente cuando alguien usa los editores de
`Editores/` (ver `Editores/MANUAL.md`) y guarda. No hace falta crear nada
aquí a mano.

## `<nombre_del_fondo>_hitboxes.json` (de `hitbox_editor.py`)

```json
{
  "image": "Imagenes/Fondos/fondo_ciudad.png",
  "image_size": [1296, 810],
  "hitboxes": [
    {"type": "rect", "role": "wall", "rx": 0.12, "ry": 0.56, "rw": 0.08, "rh": 0.07},
    {"type": "rect", "role": "interactable", "rx": 0.52, "ry": 0.33,
     "rw": 0.06, "rh": 0.10, "action": "puerta", "target_image": ""}
  ],
  "spawn": {},
  "npc_positions": {},
  "decoracion": []
}
```

Lo importante:

- Las coordenadas **son proporciones de 0 a 1**, no píxeles: `rx`/`ry` son la
  esquina superior izquierda y `rw`/`rh` el ancho y alto, todo relativo al
  tamaño de la imagen. Para pasarlas a píxeles en el juego hay que
  multiplicar por el tamaño real del fondo en pantalla. La ventaja es que
  siguen siendo válidas aunque el fondo se reescale.
- `type` puede ser `"rect"`, `"circle"` (usa `cx`, `cy`, `r`) o `"line"`
  (usa `x1`, `y1`, `x2`, `y2` y un grosor).
- `role` es `"wall"` (pared, bloquea el paso) o `"interactable"` (zona con la
  que el jugador puede interactuar).
- Los interactuables traen además `action` y `target_image`, pensados para
  puertas que llevan a otra escena. En Alcalde Digital todavía no hay
  escenas conectadas, así que esos campos se pueden dejar como vengan.
- `spawn`, `npc_positions` y `decoracion` son secciones que vienen del
  editor de EmpatiaQuest. Aquí van a quedar vacías salvo el punto de inicio
  del modo de prueba (`spawn`), que solo sirve dentro del editor.

**Pendiente:** todavía no hay código en `App.py` ni en `screens/ciudad.py`
que cargue estos archivos para bloquear el movimiento contra las paredes. El
editor los genera y los puedes probar ahí mismo con su modo de prueba
(tecla `T`), pero falta conectarlos con la pantalla real del juego — y al
hacerlo hay que acordarse de desnormalizar las coordenadas.

## `<nombre_del_personaje>_config.json` (de `personaje_editor.py`)

Escala y los dos hitboxes de un personaje, como proporciones relativas al
tamaño de su sprite. **Es el mismo formato que lee `Movimiento/Personaje.py`:**

```json
{
  "scale": 1.6,
  "hitbox_w_ratio": 0.20,
  "hitbox_h_ratio": 0.12,
  "hitbox_offset_x_ratio": 0.40,
  "hitbox_offset_y_ratio": 0.86,
  "interactable_hitbox_w_ratio": 0.32,
  "interactable_hitbox_h_ratio": 0.22,
  "interactable_hitbox_offset_x_ratio": 0.34,
  "interactable_hitbox_offset_y_ratio": 0.72
}
```

Las claves `hitbox_*` son el hitbox de colisión (con qué choca el personaje).
Las `interactable_hitbox_*` son el de interacción (dónde otro jugador puede
interactuar con él), normalmente un poco más grande.

Cada personaje guarda su propio archivo, con el nombre de su sprite: por
ejemplo `ciudadano_idle.png` genera `Hitboxes/ciudadano_idle_config.json`.
Así calibrar el Periodista no pisa lo del Ciudadano. `personaje_config.json`
(sin prefijo) sigue funcionando como config por defecto para cualquier
personaje que todavía no tenga el suyo.

**Importante sobre el formato de sprite:** `Movimiento/Personaje.py` espera
una carpeta con 8 imágenes por personaje (`walk_down.png`, `walk_up.png`,
`walk_left.png`, `walk_right.png` y sus `idle_*`), no una sola imagen
estática como las que pide `ASSETS_PENDIENTES.md`. Es una decisión pendiente
con el equipo: o piden sprites animados por dirección (bastante más trabajo
de arte) o se simplifica el movimiento para funcionar con una imagen por
personaje.
