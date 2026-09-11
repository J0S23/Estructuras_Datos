import json
import os

import pygame


class PersonajeEditor:
    """Editor mínimo para ajustar hitbox del personaje y escala."""

    def __init__(self, ruta_sprite, width=800, height=600):
        self.ruta_sprite = ruta_sprite
        self.width = width
        self.height = height
        self.running = True
        self.scale = 1.0
        self.hitbox_w_ratio = 0.20
        self.hitbox_h_ratio = 0.12
        self.hitbox_offset_x_ratio = 0.40
        self.hitbox_offset_y_ratio = 0.88
        self.surface = pygame.Surface((width, height))
        self.image = pygame.image.load(ruta_sprite).convert_alpha()

    def guardar(self, path):
        payload = {
            "scale": self.scale,
            "hitbox_w_ratio": self.hitbox_w_ratio,
            "hitbox_h_ratio": self.hitbox_h_ratio,
            "hitbox_offset_x_ratio": self.hitbox_offset_x_ratio,
            "hitbox_offset_y_ratio": self.hitbox_offset_y_ratio,
        }
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=True, indent=2)

    def run(self):
        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height))
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_RETURN:
                        self.guardar(os.path.join("Hitboxes", "personaje_config.json"))
                    elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                        self.scale += 0.05
                    elif event.key == pygame.K_MINUS:
                        self.scale = max(0.2, self.scale - 0.05)
                    elif event.key == pygame.K_LEFT:
                        self.hitbox_offset_x_ratio = max(0.0, self.hitbox_offset_x_ratio - 0.01)
                    elif event.key == pygame.K_RIGHT:
                        self.hitbox_offset_x_ratio = min(1.0, self.hitbox_offset_x_ratio + 0.01)
                    elif event.key == pygame.K_UP:
                        self.hitbox_offset_y_ratio = max(0.0, self.hitbox_offset_y_ratio - 0.01)
                    elif event.key == pygame.K_DOWN:
                        self.hitbox_offset_y_ratio = min(1.0, self.hitbox_offset_y_ratio + 0.01)
            screen.fill((30, 30, 40))
            x = (self.width - self.image.get_width()) // 2
            y = (self.height - self.image.get_height()) // 2
            screen.blit(self.image, (x, y))
            rect = pygame.Rect(x + int(self.image.get_width() * self.hitbox_offset_x_ratio), y + int(self.image.get_height() * self.hitbox_offset_y_ratio), max(10, int(self.image.get_width() * self.hitbox_w_ratio)), max(10, int(self.image.get_height() * self.hitbox_h_ratio)))
            pygame.draw.rect(screen, (255, 0, 0), rect, 2)
            pygame.display.flip()
            clock.tick(60)
        pygame.quit()


if __name__ == "__main__":
    PersonajeEditor("Imagenes/Personajes/ciudadano_idle.png").run()
