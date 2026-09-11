"""Estado básico del juego para Alcalde Digital."""

from config import INDICADORES_CIUDAD_INICIALES


class GameState:
    def __init__(self):
        self.indicadores = dict(INDICADORES_CIUDAD_INICIALES)
        self.rol_actual = "Ciudadano"
        self.puntaje = 0
        self.publicaciones_vistas = []

    def actualizar_indicador(self, nombre, delta):
        if nombre not in self.indicadores:
            self.indicadores[nombre] = 0
        self.indicadores[nombre] = max(0, min(100, self.indicadores[nombre] + int(delta)))

    def to_dict(self):
        return {
            "rol_actual": self.rol_actual,
            "puntaje": self.puntaje,
            "indicadores": self.indicadores,
            "publicaciones_vistas": self.publicaciones_vistas,
        }
