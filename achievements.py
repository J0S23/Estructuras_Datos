import json
import os


RARITY_COLORS = {
    "comun": (90, 190, 255),
    "raro": (120, 220, 140),
    "epico": (190, 120, 255),
    "oculto": (255, 185, 60),
}


class AchievementData:
    def __init__(self, id, nombre, descripcion, categoria, rareza="comun",
                 objetivo=1, secreto=False, icono="", condition=None,
                 progress=None):
        self.id = id
        self.nombre = nombre
        self.descripcion = descripcion
        self.categoria = categoria
        self.rareza = rareza
        self.objetivo = objetivo
        self.secreto = secreto
        self.icono = icono
        self.condition = condition
        self.progress = progress


class Logro:
    def __init__(self, id, nombre, descripcion, categoria="General",
                 rareza="comun", objetivo=1, secreto=False, icono="",
                 completo=False, progreso=0, unlocked_at=0, _data=None):
        self.id = id
        self.nombre = nombre
        self.descripcion = descripcion
        self.categoria = categoria
        self.rareza = rareza
        self.objetivo = objetivo
        self.secreto = secreto
        self.icono = icono
        self.completo = completo
        self.progreso = progreso
        self.unlocked_at = unlocked_at
        self._data = _data

    @property
    def porcentaje(self):
        if self.completo:
            return 100
        return int(min(100, (self.progreso / max(1, self.objetivo)) * 100))

    @property
    def descripcion_visible(self):
        if self.secreto and not self.completo:
            return "Logro secreto. Se revelara al desbloquearlo."
        return self.descripcion

    def to_dict(self):
        return {
            "id": self.id,
            "completo": self.completo,
            "progreso": self.progreso,
            "unlocked_at": self.unlocked_at,
        }

    @classmethod
    def from_data(cls, data):
        return cls(
            id=data.id,
            nombre=data.nombre,
            descripcion=data.descripcion,
            categoria=data.categoria,
            rareza=data.rareza,
            objetivo=data.objetivo,
            secreto=data.secreto,
            icono=data.icono,
            _data=data,
        )


class AchievementTracker:
    """Guarda hechos normalizados que las condiciones de logros usan."""

    def __init__(self):
        self.contadores = {}
        self.flags = set()

    def registrar_evento(self, nombre, cantidad=1):
        self.contadores[nombre] = self.contadores.get(nombre, 0) + cantidad

    def marcar_flag(self, nombre):
        self.flags.add(nombre)

    def to_dict(self):
        return {"contadores": self.contadores, "flags": list(self.flags)}

    def load(self, data):
        self.contadores = dict(data.get("contadores", {}))
        self.flags = set(data.get("flags", []))


class AchievementManager:
    def __init__(self, save_file, definiciones):
        self.save_file = save_file
        self.tracker = AchievementTracker()
        self.logros = {}
        for definicion in definiciones:
            self.logros[definicion.id] = Logro.from_data(definicion)
        self._dirty = False

    def to_list(self):
        resultado = []
        for logro in self.logros.values():
            resultado.append(logro.to_dict())
        return resultado

    def load_global(self):
        try:
            with open(self.save_file, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(data, dict):
            return
        self.tracker.load(data.get("tracker", {}))
        for item in data.get("logros", []):
            if isinstance(item, dict):
                logro = self.logros.get(str(item.get("id", "")))
                if logro is not None:
                    logro.completo = bool(item.get("completo", False))
                    logro.progreso = int(item.get("progreso", 0))
                    logro.unlocked_at = int(item.get("unlocked_at", 0))

    def save_global(self):
        os.makedirs(os.path.dirname(self.save_file), exist_ok=True)
        payload = {
            "save_version": 1,
            "logros": self.to_list(),
            "tracker": self.tracker.to_dict(),
        }
        try:
            with open(self.save_file, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=True, indent=2)
            self._dirty = False
        except OSError:
            pass

    def completados(self):
        resultado = []
        for logro in self.logros.values():
            if logro.completo:
                resultado.append(logro)
        return resultado

    def todos(self):
        return list(self.logros.values())

    def porcentaje(self):
        total = len(self.logros)
        return int((len(self.completados()) / total) * 100) if total else 0


class AchievementUI:
    @staticmethod
    def rarity_color(rareza):
        return RARITY_COLORS.get(rareza, RARITY_COLORS["comun"])


class Lista_Logros(AchievementManager):
    """Alias retrocompatible."""


LOGRO_TRIGGERS = {}


DEFINICIONES_LOGROS_ALCALDE_DIGITAL = [
    AchievementData(
        id="primer_verificado",
        nombre="Primera verificación",
        descripcion="Verificas una publicación antes de compartirla.",
        categoria="Ciudad",
        rareza="comun",
        objetivo=1,
        secreto=False,
    ),
    AchievementData(
        id="rumor_desmantelado",
        nombre="Rumor desmontado",
        descripcion="Reportas un rumor falso antes de que se difunda.",
        categoria="Ciudad",
        rareza="raro",
        objetivo=1,
        secreto=False,
    ),
    AchievementData(
        id="fuente_credible",
        nombre="Fuente creíble",
        descripcion="Usas la verificación para construir confianza ciudadana.",
        categoria="Periodo",
        rareza="raro",
        objetivo=3,
        secreto=False,
    ),
    AchievementData(
        id="influencer_responsable",
        nombre="Influencer responsable",
        descripcion="Compartes información verificando su origen.",
        categoria="Redes",
        rareza="epico",
        objetivo=5,
        secreto=False,
    ),
    AchievementData(
        id="alcalde_justo",
        nombre="Alcalde justo",
        descripcion="Logras equilibrar indicadores de la ciudad.",
        categoria="Gobierno",
        rareza="oculto",
        objetivo=1,
        secreto=True,
    ),
]
