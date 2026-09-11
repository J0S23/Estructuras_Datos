import json
import os

import pygame


class HitboxEditor:
    """Editor mínimo para marcar paredes y objetos interactuables."""

    def __init__(self, ruta_fondo=None, width=1000, height=700):
        self.width = width
        self.height = height
        self.running = True
        self.ruta_fondo = ruta_fondo
        self.rects = []
        self.dragging = False
        self.start_pos = None
        self.current_type = "wall"

    def _load_background(self):
        if self.ruta_fondo and os.path.exists(self.ruta_fondo):
            return pygame.image.load(self.ruta_fondo).convert()
        return None

    def guardar(self, path):
        payload = [{"x": r[0], "y": r[1], "w": r[2], "h": r[3], "tipo": r[4]} for r in self.rects]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=True, indent=2)

    def run(self):
        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height))
        clock = pygame.time.Clock()
        background = self._load_background()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_s:
                        self.guardar(os.path.join("Hitboxes", "escenario_hitboxes.json"))
                    elif event.key == pygame.K_t:
                        self.current_type = "interactable" if self.current_type == "wall" else "wall"
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.dragging = True
                    self.start_pos = event.pos
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.start_pos is not None:
                        x1, y1 = self.start_pos
                        x2, y2 = event.pos
                        rect = pygame.Rect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
                        if rect.w > 2 and rect.h > 2:
                            self.rects.append((rect.x, rect.y, rect.w, rect.h, self.current_type))
                    self.dragging = False
                    self.start_pos = None

            screen.fill((20, 20, 25))
            if background is not None:
                screen.blit(background, (0, 0))
            for rect in self.rects:
                x, y, w, h, tipo = rect
                color = (255, 140, 70) if tipo == "interactable" else (90, 180, 255)
                pygame.draw.rect(screen, color, (x, y, w, h), 2)
            if self.dragging and self.start_pos is not None:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                rect = pygame.Rect(self.start_pos[0], self.start_pos[1], mouse_x - self.start_pos[0], mouse_y - self.start_pos[1])
                pygame.draw.rect(screen, (255, 255, 255), rect, 2)
            pygame.display.flip()
            clock.tick(60)
        pygame.quit()


if __name__ == "__main__":
    HitboxEditor().run()
