# Alcalde Digital

Alcalde Digital es un videojuego educativo en Python/Pygame sobre el consumo responsable de información, la verificación de noticias y la gestión de la confianza ciudadana en redes sociales.

## ¿Qué hace este proyecto?

El juego simula una ciudad donde el jugador toma decisiones sobre publicaciones, rumores, noticias y relaciones sociales. La idea central es que cada decisión afecta indicadores como:

- información verificada
- confianza ciudadana
- convivencia
- bienestar digital
- desinformación
- conflictos

Estos indicadores se usan para medir si la ciudad mejora o empeora según las decisiones del jugador.

## Mini resumen de la arquitectura

### Módulos principales

- `main.py`: punto de entrada del juego. Aquí se inicializa la lógica principal y se prueba la estructura de datos.
- `config.py`: almacena constantes del proyecto, colores, ajustes por defecto, roles de juego e indicadores globales.
- `game_state.py`: mantiene el estado del juego: rol actual, puntaje e indicadores de la ciudad.
- `renderer.py`: contiene funciones básicas de renderizado, como dibujar texto y paneles. Sirve como capa simple de visualización antes de que exista una interfaz más completa.
- `audio_manager.py`: gestiona música de fondo y efectos de sonido; si no encuentra archivos reales, usa tonos sencillos para no romper la ejecución.
- `transition_manager.py`: administra transiciones entre pantallas con fade in/out.
- `achievements.py`: define logros y rastreo de progreso para recompensas del jugador.
- `screen_handlers.py`: módulo auxiliar para compatibilidad con pantallas y manejo general.

### Movimiento y personajes

- `Movimiento/Personaje.py`: carga sprites, calcula hitboxes y controla movimiento del personaje con animaciones.
- `Movimiento/Animacion.py`: maneja frames de animación y desplazamiento lateral.
- `Movimiento/Fondo.py`: carga y dibuja fondos de escena.

### Estructuras de datos

- `Estructuras/nodo_decision.py`: nodo de un árbol de decisiones.
- `Estructuras/arbol_decision.py`: árbol N-ario para modelar decisiones y consecuencias de una publicación.
- `Estructuras/nodo_abb.py`: nodo de un árbol binario de búsqueda.
- `Estructuras/abb_publicaciones.py`: ABB para guardar publicaciones ordenadas por veracidad.

### Pantallas

- `screens/menu.py`: pantalla inicial.
- `screens/ciudad.py`: escena de ciudad.
- `screens/publicacion.py`: pantalla para mostrar publicaciones y decisiones.
- `screens/ayuda.py`: guía del juego y explicación de indicadores.
- `screens/creditos.py`: créditos con scroll simple.

### Datos y contenido

- `data/publicaciones_ejemplo.py`: ejemplos de publicaciones con opciones y efectos en indicadores.
- `Hitboxes/`: directorio para configuraciones de colisiones.
- `Imagenes/`: recursos visuales esperados para personajes, fondos e interfaz.
- `Audio/`: música y efectos de sonido esperados.

## Requisitos

- Python 3.11+
- Pygame

## Cómo correrlo

Ejecuta desde la raíz del proyecto:

```bash
python main.py
```

## Estructura de carpetas

- `main.py`: punto de entrada del proyecto.
- `config.py`: constantes, colores y configuración global.
- `renderer.py`: renderizado básico de texto y paneles.
- `game_state.py`: estado del juego.
- `audio_manager.py`: música y efectos.
- `transition_manager.py`: transiciones de pantalla.
- `achievements.py`: logros y progresos.
- `Movimiento/`: animación y movimiento del personaje.
- `Estructuras/`: árboles de decisión y ABB para publicaciones.
- `screens/`: pantallas del juego.
- `data/`: datos de ejemplo del proyecto.
- `Editores/`: herramientas simples para diseñar hitboxes y ajustar personajes.

## Créditos técnicos

El sistema de hitboxes, movimiento, audio y logros está adaptado a partir de patrones del proyecto EmpatiaQuest, reimplementados y simplificados para esta entrega.
