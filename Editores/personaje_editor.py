"""
Editor de personaje + Hitboxes de Minijuego — EmpatiaQuest
- Selector visual de personajes/imágenes al inicio.
- Escala e hitboxes independientes por asset (cada uno tiene su propio config).
- Assets de minijuego (Corazon/Puño/Mensaje): solo hitbox roja, sin amarilla,
  scale se refleja en el minijuego.
"""
import json
import os
import sys
import pygame

# ─── Rutas de config ──────────────────────────────────────────────────────────
# El juego SOLO lee personaje_config.json (para el personaje principal).
# Todos los demás usan archivos independientes en Hitboxes/.
MAIN_CHARACTER_FOLDER = "personaje_main"
PERSONAJE_CONFIG_NAME = os.path.join("Hitboxes", "personaje_config.json")
MINIJUEGO_CONFIG_NAME = os.path.join("Hitboxes", "minijuego_config.json")

DEFAULT_SCALE = 1.6
MAX_SCALE     = 12.0
DEFAULT_HB    = {"w_ratio": 0.20, "h_ratio": 0.12,
                 "offset_x_ratio": 0.40, "offset_y_ratio": 0.86}

MINI_HITBOX_DEFAULTS = {
    "heart":   {"w_ratio": 0.50, "h_ratio": 0.50, "offset_x_ratio": 0.25, "offset_y_ratio": 0.25, "scale": 4.0},
    "fist":    {"w_ratio": 0.50, "h_ratio": 0.50, "offset_x_ratio": 0.25, "offset_y_ratio": 0.25, "scale": 4.0},
    "message": {"w_ratio": 0.70, "h_ratio": 0.60, "offset_x_ratio": 0.15, "offset_y_ratio": 0.20, "scale": 3.0},
}

# ─── Colores ──────────────────────────────────────────────────────────────────
C_BG      = (22, 24, 36)
C_PANEL   = (34, 38, 56)
C_PANEL2  = (28, 32, 48)
C_BORDER  = (70, 80, 120)
C_SEL     = (55, 70, 130)
C_SEL_BDR = (110, 140, 220)
C_TEXT    = (230, 235, 255)
C_SOFT    = (140, 150, 190)
C_TITLE   = (200, 215, 255)
C_ACCENT  = (80, 160, 255)
C_RED     = (220, 60, 60)
C_YELLOW  = (255, 210, 40)
C_ORANGE  = (255, 140, 30)
C_BLUE    = (80, 190, 255)
C_GREEN   = (80, 210, 120)


# ─── Utilidades ───────────────────────────────────────────────────────────────

def clamp01(v):
    return max(0.0, min(1.0, v))

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def draw_text(surf, text, x, y, font, color=C_TEXT):
    for i, line in enumerate(text.split("\n")):
        s = font.render(line, True, color)
        surf.blit(s, (x, y + i * (s.get_height() + 3)))

def read_hitbox(cfg, prefix, defaults):
    return {k: float(cfg.get(f"{prefix}_{k}", defaults[k])) for k in defaults}

def load_thumb(path, size=80):
    try:
        img = pygame.image.load(path).convert_alpha()
        w, h = img.get_size()
        sc = min(size / w, size / h)
        return pygame.transform.smoothscale(img, (max(1, int(w * sc)), max(1, int(h * sc))))
    except Exception:
        return None


# ─── Detección de asset de minijuego ─────────────────────────────────────────

def get_minijuego_key(sprite_path):
    """Devuelve 'heart', 'fist', 'message' o None según el sprite."""
    marker = os.path.join("Minijuegos", "Undertale")
    if marker not in sprite_path and "Minijuegos" not in sprite_path:
        return None
    fname = os.path.basename(sprite_path).lower()
    # Normalizar: quitar acentos del comparador
    fname_n = fname.replace("ó", "o").replace("ñ", "n")
    if "corazon" in fname_n or "corazon" in fname_n:
        return "heart"
    if "puno" in fname_n or "fist" in fname_n or "puno" in fname_n:
        return "fist"
    if "mensaje" in fname_n or "message" in fname_n:
        return "message"
    return None


def get_char_config_path(sprite_path, project_root):
    """Cada personaje guarda su propio config: Hitboxes/<nombre_del_sprite>_config.json.

    Antes todos compartían personaje_config.json, así que calibrar un rol
    (Periodista, Influencer...) pisaba la calibración del anterior. Con un
    archivo por sprite cada rol conserva el suyo.
    """
    nombre = os.path.splitext(os.path.basename(sprite_path))[0]
    return os.path.join(project_root, "Hitboxes", f"{nombre}_config.json")


def load_char_config(sprite_path, project_root):
    """Lee el config propio del personaje; si todavía no tiene uno, parte del
    personaje_config.json general para no arrancar de cero."""
    cfg = load_json(get_char_config_path(sprite_path, project_root))
    if cfg:
        return cfg
    return load_json(os.path.join(project_root, PERSONAJE_CONFIG_NAME))


# ─── Colección de entradas para el selector ───────────────────────────────────

def collect_entries(project_root):
    entries = []
    img_root = os.path.join(project_root, "Imagenes")

    # Personajes: solo la pose "idle/parado" por carpeta (búsqueda case-insensitive)
    personajes_dir = os.path.join(img_root, "Personajes")
    if os.path.isdir(personajes_dir):
        idle_keywords = ["idle_down", "idle", "parado", "stand"]
        for char_name in sorted(os.listdir(personajes_dir)):
            char_dir = os.path.join(personajes_dir, char_name)
            if not os.path.isdir(char_dir):
                if char_name.lower().endswith(".png"):
                    entries.append({
                        "label": f"[Personaje] {char_name}",
                        "path":  os.path.join(personajes_dir, char_name),
                        "thumb": None,
                    })
                continue
            all_pngs = sorted(f for f in os.listdir(char_dir) if f.lower().endswith(".png"))
            sprite_file = None
            for kw in idle_keywords:
                for png in all_pngs:
                    if kw in png.lower():
                        sprite_file = os.path.join(char_dir, png)
                        break
                if sprite_file:
                    break
            if sprite_file is None and all_pngs:
                sprite_file = os.path.join(char_dir, all_pngs[0])
            if sprite_file:
                entries.append({
                    "label": f"[Personaje] {char_name}",
                    "path":  sprite_file,
                    "thumb": None,
                })

    # Interactuables y Escenarios
    for section in ("Interactuables", "Escenarios"):
        base = os.path.join(img_root, section)
        if not os.path.isdir(base):
            continue
        for item in sorted(os.listdir(base)):
            item_path = os.path.join(base, item)
            if item.lower().endswith(".png") and os.path.isfile(item_path):
                entries.append({"label": f"[{section}] {item}", "path": item_path, "thumb": None})
            elif os.path.isdir(item_path):
                for fname in sorted(f for f in os.listdir(item_path) if f.lower().endswith(".png")):
                    entries.append({
                        "label": f"[{section}/{item}] {fname}",
                        "path":  os.path.join(item_path, fname),
                        "thumb": None,
                    })

    # Assets de minijuego (Corazon, Puño, Mensajes)
    mini_dir = os.path.join(img_root, "Minijuegos", "Undertale")
    if os.path.isdir(mini_dir):
        priority = ["Corazon.png", "Puño.png"]
        all_pngs = sorted(f for f in os.listdir(mini_dir) if f.lower().endswith(".png"))
        ordered  = [f for f in priority if f in all_pngs]
        # Solo UN representante de mensajes — todos comparten la clave "message"
        msg_repr = None
        for f in all_pngs:
            if f not in priority:
                full = os.path.join(mini_dir, f)
                if get_minijuego_key(full) == "message":
                    if msg_repr is None:
                        msg_repr = f   # primer mensaje encontrado = representante
                    # los demás se omiten (misma hitbox/escala)
                else:
                    ordered.append(f)  # otros assets no-mensaje se incluyen
        if msg_repr:
            ordered.append(msg_repr)
        for fname in ordered:
            is_msg = (fname == msg_repr)
            label  = "[Minijuego] Mensajes (compartido)" if is_msg else f"[Minijuego] {fname}"
            entries.append({
                "label": label,
                "path":  os.path.join(mini_dir, fname),
                "thumb": None,
            })

    return entries


# ─── Pantalla de selección ────────────────────────────────────────────────────

def run_selector(screen, clock, project_root):
    font_title = pygame.font.SysFont("consolas", 26, bold=True)
    font_item  = pygame.font.SysFont("consolas", 17)
    font_small = pygame.font.SysFont("consolas", 14)

    sw, sh = screen.get_size()
    entries = collect_entries(project_root)
    if not entries:
        return None

    sel_idx    = 0
    scroll_off = 0
    ROW_H      = 54
    LIST_X, LIST_Y = 40, 100
    LIST_W = sw - 300
    LIST_H = sh - 160
    VISIBLE    = LIST_H // ROW_H
    PREVIEW_X  = LIST_X + LIST_W + 20
    PREVIEW_Y  = LIST_Y
    PREVIEW_W  = sw - PREVIEW_X - 20
    PREVIEW_H  = sh - LIST_Y - 60

    search_text   = ""
    search_active = False
    preview_surf  = None
    prev_path     = None

    def filtered():
        if not search_text:
            return entries
        low = search_text.lower()
        return [e for e in entries if low in e["label"].lower()]

    def get_preview(path):
        nonlocal preview_surf, prev_path
        if path == prev_path:
            return preview_surf
        prev_path = path
        try:
            img = pygame.image.load(path).convert_alpha()
            w, h = img.get_size()
            sc = min((PREVIEW_W - 10) / w, (PREVIEW_H - 10) / h)
            preview_surf = pygame.transform.smoothscale(img, (max(1, int(w * sc)), max(1, int(h * sc))))
        except Exception:
            preview_surf = None
        return preview_surf

    running = True
    while running:
        vis = filtered()
        sel_idx    = max(0, min(sel_idx, len(vis) - 1))
        scroll_off = max(0, min(scroll_off, max(0, len(vis) - VISIBLE)))
        if sel_idx < scroll_off:
            scroll_off = sel_idx
        elif sel_idx >= scroll_off + VISIBLE:
            scroll_off = sel_idx - VISIBLE + 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.KEYDOWN:
                if search_active:
                    if event.key == pygame.K_ESCAPE:
                        search_active = False; search_text = ""
                    elif event.key == pygame.K_RETURN:
                        search_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        search_text = search_text[:-1]
                    else:
                        ch = event.unicode
                        if ch.isprintable():
                            search_text += ch
                    sel_idx = 0
                    continue
                if event.key == pygame.K_ESCAPE:
                    return None
                elif event.key == pygame.K_UP:
                    sel_idx = max(0, sel_idx - 1)
                elif event.key == pygame.K_DOWN:
                    sel_idx = min(len(vis) - 1, sel_idx + 1)
                elif event.key == pygame.K_PAGEUP:
                    sel_idx = max(0, sel_idx - VISIBLE)
                elif event.key == pygame.K_PAGEDOWN:
                    sel_idx = min(len(vis) - 1, sel_idx + VISIBLE)
                elif event.key == pygame.K_HOME:
                    sel_idx = 0
                elif event.key == pygame.K_END:
                    sel_idx = max(0, len(vis) - 1)
                elif event.key == pygame.K_RETURN and vis:
                    return vis[sel_idx]["path"]
                elif event.key == pygame.K_f and event.mod & pygame.KMOD_CTRL:
                    search_active = True; search_text = ""
            elif event.type == pygame.MOUSEWHEEL:
                sel_idx = max(0, min(len(vis) - 1, sel_idx - event.y))
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                for i in range(VISIBLE):
                    idx = scroll_off + i
                    if idx >= len(vis):
                        break
                    row = pygame.Rect(LIST_X, LIST_Y + i * ROW_H, LIST_W, ROW_H - 2)
                    if row.collidepoint(mx, my):
                        if idx == sel_idx and event.button == 1:
                            return vis[sel_idx]["path"]
                        sel_idx = idx

        # ── Dibujo ────────────────────────────────────────────────────────────
        screen.fill(C_BG)
        t = font_title.render("Selecciona imagen para editar hitboxes", True, C_TITLE)
        screen.blit(t, (LIST_X, 30))
        hint = font_small.render("↑↓ navegar   ENTER seleccionar   Ctrl+F buscar   ESC salir", True, C_SOFT)
        screen.blit(hint, (LIST_X, 66))

        pygame.draw.rect(screen, C_PANEL,  (LIST_X-8, LIST_Y-8, LIST_W+16, LIST_H+16), border_radius=8)
        pygame.draw.rect(screen, C_BORDER, (LIST_X-8, LIST_Y-8, LIST_W+16, LIST_H+16), 2, border_radius=8)

        for i in range(VISIBLE):
            idx = scroll_off + i
            if idx >= len(vis):
                break
            entry    = vis[idx]
            row_rect = pygame.Rect(LIST_X, LIST_Y + i * ROW_H, LIST_W, ROW_H - 2)
            is_sel   = idx == sel_idx
            if is_sel:
                pygame.draw.rect(screen, C_SEL,     row_rect, border_radius=5)
                pygame.draw.rect(screen, C_SEL_BDR, row_rect, 2, border_radius=5)
            elif i % 2 == 0:
                pygame.draw.rect(screen, (38, 42, 60), row_rect, border_radius=4)
            if entry["thumb"] is None:
                entry["thumb"] = load_thumb(entry["path"], 44)
            if entry["thumb"]:
                th = entry["thumb"]
                screen.blit(th, (row_rect.x + 6, row_rect.centery - th.get_height() // 2))
                tx = row_rect.x + 56
            else:
                pygame.draw.rect(screen, C_BORDER, (row_rect.x+6, row_rect.y+8, 40, 36), 1)
                tx = row_rect.x + 56
            color = C_TEXT if is_sel else C_SOFT
            lbl = font_item.render(entry["label"], True, color)
            screen.blit(lbl, (tx, row_rect.centery - lbl.get_height() // 2))

        if len(vis) > VISIBLE:
            sb_x = LIST_X + LIST_W + 4
            sb_h = LIST_H
            pygame.draw.rect(screen, C_PANEL2, (sb_x, LIST_Y, 8, sb_h), border_radius=4)
            thumb_h = max(20, sb_h * VISIBLE // max(1, len(vis)))
            thumb_y = LIST_Y + (sb_h - thumb_h) * scroll_off // max(1, len(vis) - VISIBLE)
            pygame.draw.rect(screen, C_ACCENT, (sb_x, thumb_y, 8, thumb_h), border_radius=4)

        # Preview
        if vis and 0 <= sel_idx < len(vis):
            path = vis[sel_idx]["path"]
            prev = get_preview(path)
            pygame.draw.rect(screen, C_PANEL,  (PREVIEW_X-8, PREVIEW_Y-8, PREVIEW_W+16, PREVIEW_H+16), border_radius=8)
            pygame.draw.rect(screen, C_BORDER, (PREVIEW_X-8, PREVIEW_Y-8, PREVIEW_W+16, PREVIEW_H+16), 2, border_radius=8)
            if prev:
                px = PREVIEW_X + (PREVIEW_W - prev.get_width())  // 2
                py = PREVIEW_Y + (PREVIEW_H - prev.get_height()) // 2
                screen.blit(prev, (px, py))
            fname_lbl = font_small.render(os.path.basename(path), True, C_SOFT)
            screen.blit(fname_lbl, (PREVIEW_X, PREVIEW_Y + PREVIEW_H + 6))

        if search_active:
            sb_rect = pygame.Rect(LIST_X, sh - 44, LIST_W, 32)
            pygame.draw.rect(screen, (20, 24, 40), sb_rect, border_radius=5)
            pygame.draw.rect(screen, C_ACCENT, sb_rect, 2, border_radius=5)
            screen.blit(font_item.render(f"Buscar: {search_text}_", True, C_TEXT), (sb_rect.x+8, sb_rect.y+6))
        elif search_text:
            screen.blit(font_small.render(f"Filtro: '{search_text}'  (Ctrl+F editar)", True, C_ACCENT), (LIST_X, sh-30))

        cnt = font_small.render(f"{len(vis)} entradas", True, C_SOFT)
        screen.blit(cnt, (LIST_X + LIST_W - cnt.get_width(), LIST_Y - 26))
        pygame.display.flip()
        clock.tick(60)

    return None


# ─── Editor principal ─────────────────────────────────────────────────────────

def run_editor(screen, clock, sprite_path, project_root):
    mj_key = get_minijuego_key(sprite_path)

    font       = pygame.font.SysFont("consolas", 18)
    title_font = pygame.font.SysFont("consolas", 22, bold=True)
    small_font = pygame.font.SysFont("consolas", 14)

    try:
        image = pygame.image.load(sprite_path).convert_alpha()
    except Exception as e:
        print(f"Error cargando imagen: {e}")
        return
    iw_raw, ih_raw = image.get_size()

    # Animación de caminata (personajes)
    walk_frames = []
    if not mj_key:
        walk_dir  = os.path.dirname(sprite_path)
        for wname in ("walk_down.png", "walk_down_0.png"):
            wpath = os.path.join(walk_dir, wname)
            if os.path.exists(wpath):
                try:
                    ws = pygame.image.load(wpath).convert_alpha()
                    wsw, wsh = ws.get_size()
                    wfc = max(1, round(wsw / max(1, wsh)))
                    wfw = wsw // wfc
                    walk_frames = [ws.subsurface(pygame.Rect(i*wfw, 0, wfw, wsh)).copy() for i in range(wfc)]
                except Exception:
                    pass
                break

    # ── Cargar estado ─────────────────────────────────────────────────────────
    if mj_key:
        # Assets de minijuego: config en minijuego_config.json bajo la clave mj_key
        mj_config_path = os.path.join(project_root, MINIJUEGO_CONFIG_NAME)
        mj_cfg_all = load_json(mj_config_path)
        stored = mj_cfg_all.get(mj_key, {})
        defaults = MINI_HITBOX_DEFAULTS[mj_key]
        scale = float(stored.get("scale", defaults["scale"]))
        hitboxes = {
            "collision": {k: float(stored.get(k, defaults[k]))
                          for k in ("w_ratio", "h_ratio", "offset_x_ratio", "offset_y_ratio")},
        }
        config_path = mj_config_path  # referencia para saber a dónde guardar
    else:
        # Personaje: config independiente por carpeta
        config_path = get_char_config_path(sprite_path, project_root)
        cfg = load_char_config(sprite_path, project_root)
        scale = float(cfg.get("scale", DEFAULT_SCALE))
        hitboxes = {
            "collision":    read_hitbox(cfg, "hitbox",             DEFAULT_HB),
            "interactable": read_hitbox(cfg, "interactable_hitbox", DEFAULT_HB),
        }

    active_hb = "collision"

    # Historial
    def snapshot():
        s = {"scale": scale, "hitboxes": {k: dict(v) for k, v in hitboxes.items()}, "active_hb": active_hb}
        return s
    history = [snapshot()]
    history_idx = 0

    def push():
        nonlocal history, history_idx
        history = history[:history_idx + 1]
        history.append(snapshot())
        history_idx = len(history) - 1

    def restore(state):
        nonlocal scale, hitboxes, active_hb
        scale     = state["scale"]
        hitboxes  = {k: dict(v) for k, v in state["hitboxes"].items()}
        active_hb = state["active_hb"]

    sw, sh = screen.get_size()
    status_msg   = ""
    status_timer = 0
    running      = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                k, mod = event.key, event.mod

                if k == pygame.K_ESCAPE:
                    running = False

                # Escala
                elif k == pygame.K_q:
                    scale = max(0.1, scale - 0.05); push()
                elif k == pygame.K_e:
                    scale = min(MAX_SCALE, scale + 0.05); push()

                # Hitbox activa (roja o amarilla según active_hb)
                elif k == pygame.K_a:
                    hitboxes[active_hb]["w_ratio"] = clamp01(hitboxes[active_hb]["w_ratio"] - 0.01); push()
                elif k == pygame.K_d:
                    hitboxes[active_hb]["w_ratio"] = clamp01(hitboxes[active_hb]["w_ratio"] + 0.01); push()
                elif k == pygame.K_w:
                    hitboxes[active_hb]["h_ratio"] = clamp01(hitboxes[active_hb]["h_ratio"] - 0.01); push()
                elif k == pygame.K_s:
                    hitboxes[active_hb]["h_ratio"] = clamp01(hitboxes[active_hb]["h_ratio"] + 0.01); push()
                elif k == pygame.K_LEFT:
                    hitboxes[active_hb]["offset_x_ratio"] = clamp01(hitboxes[active_hb]["offset_x_ratio"] - 0.01); push()
                elif k == pygame.K_RIGHT:
                    hitboxes[active_hb]["offset_x_ratio"] = clamp01(hitboxes[active_hb]["offset_x_ratio"] + 0.01); push()
                elif k == pygame.K_UP:
                    hitboxes[active_hb]["offset_y_ratio"] = clamp01(hitboxes[active_hb]["offset_y_ratio"] - 0.01); push()
                elif k == pygame.K_DOWN:
                    hitboxes[active_hb]["offset_y_ratio"] = clamp01(hitboxes[active_hb]["offset_y_ratio"] + 0.01); push()

                # Toggle hitbox amarilla (solo personajes)
                elif k == pygame.K_i and not mj_key:
                    active_hb = "interactable" if active_hb == "collision" else "collision"; push()

                # Reset
                elif k == pygame.K_r:
                    scale = MINI_HITBOX_DEFAULTS[mj_key]["scale"] if mj_key else DEFAULT_SCALE
                    if mj_key:
                        d = MINI_HITBOX_DEFAULTS[mj_key]
                        hitboxes["collision"] = {k2: d[k2] for k2 in ("w_ratio", "h_ratio", "offset_x_ratio", "offset_y_ratio")}
                    else:
                        hitboxes = {"collision": dict(DEFAULT_HB), "interactable": dict(DEFAULT_HB)}
                    push()

                # Undo/Redo
                elif k == pygame.K_z and mod & pygame.KMOD_CTRL:
                    if history_idx > 0:
                        history_idx -= 1; restore(history[history_idx])
                elif k == pygame.K_y and mod & pygame.KMOD_CTRL:
                    if history_idx < len(history) - 1:
                        history_idx += 1; restore(history[history_idx])

                # Guardar
                elif k == pygame.K_RETURN:
                    if mj_key:
                        mj_cfg_all = load_json(config_path)
                        mj_cfg_all[mj_key] = dict(hitboxes["collision"])
                        mj_cfg_all[mj_key]["scale"] = scale
                        save_json(config_path, mj_cfg_all)
                        status_msg = f"Guardado en minijuego_config.json [{mj_key}]"
                    else:
                        col = hitboxes["collision"]
                        itr = hitboxes.get("interactable", col)
                        save_json(config_path, {
                            "scale": scale,
                            "hitbox_w_ratio":                     col["w_ratio"],
                            "hitbox_h_ratio":                     col["h_ratio"],
                            "hitbox_offset_x_ratio":              col["offset_x_ratio"],
                            "hitbox_offset_y_ratio":              col["offset_y_ratio"],
                            "interactable_hitbox_w_ratio":        itr["w_ratio"],
                            "interactable_hitbox_h_ratio":        itr["h_ratio"],
                            "interactable_hitbox_offset_x_ratio": itr["offset_x_ratio"],
                            "interactable_hitbox_offset_y_ratio": itr["offset_y_ratio"],
                        })
                        char_name = os.path.basename(os.path.dirname(sprite_path))
                        status_msg = f"Guardado: {os.path.basename(config_path)}"
                        # Si es personaje_main, también guardamos en el path canónico
                        if char_name == MAIN_CHARACTER_FOLDER:
                            canonical = os.path.join(project_root, PERSONAJE_CONFIG_NAME)
                            if config_path != canonical:
                                save_json(canonical, load_json(config_path))
                    status_timer = 180

        # ── Render ────────────────────────────────────────────────────────────
        screen.fill(C_BG)

        scaled_w = max(1, int(iw_raw * scale))
        scaled_h = max(1, int(ih_raw * scale))
        sprite   = pygame.transform.smoothscale(image, (scaled_w, scaled_h))

        PREV_X, PREV_Y = 50, 90
        PREV_AREA_W, PREV_AREA_H = 520, 520
        spr_rect = sprite.get_rect(center=(PREV_X + PREV_AREA_W // 2, PREV_Y + PREV_AREA_H // 2))

        # Título
        asset_name = os.path.basename(sprite_path)
        title_color = C_ORANGE if mj_key else C_TITLE
        t = title_font.render(f"Editando: {asset_name}", True, title_color)
        screen.blit(t, (PREV_X - 14, 30))
        back_hint = small_font.render("ESC → volver al selector", True, C_SOFT)
        screen.blit(back_hint, (PREV_X - 14, 56))
        if mj_key:
            mk_lbl = small_font.render(f"Asset minijuego: {mj_key.upper()}  — config independiente, escala se refleja en el juego", True, C_GREEN)
            screen.blit(mk_lbl, (PREV_X - 14, 74))

        # Panel sprite
        pygame.draw.rect(screen, C_PANEL,  (PREV_X-14, PREV_Y-14, PREV_AREA_W+28, PREV_AREA_H+28), border_radius=10)
        pygame.draw.rect(screen, C_BORDER, (PREV_X-14, PREV_Y-14, PREV_AREA_W+28, PREV_AREA_H+28), 2, border_radius=10)
        screen.blit(sprite, spr_rect.topleft)

        # ── Hitbox roja (siempre) ──────────────────────────────────────────────
        col = hitboxes["collision"]
        col_rect = pygame.Rect(
            spr_rect.left + int(scaled_w * col["offset_x_ratio"]),
            spr_rect.top  + int(scaled_h * col["offset_y_ratio"]),
            max(4, int(scaled_w * col["w_ratio"])),
            max(4, int(scaled_h * col["h_ratio"])),
        )
        # Relleno semitransparente
        col_surf = pygame.Surface((col_rect.w, col_rect.h), pygame.SRCALPHA)
        col_surf.fill((220, 60, 60, 55))
        screen.blit(col_surf, (col_rect.x, col_rect.y))
        lw = 3 if active_hb == "collision" else 2
        pygame.draw.rect(screen, C_RED, col_rect, lw)
        pygame.draw.line(screen, C_RED, (spr_rect.left, col_rect.top),    (spr_rect.right, col_rect.top), 1)
        pygame.draw.line(screen, C_RED, (spr_rect.left, col_rect.bottom), (spr_rect.right, col_rect.bottom), 1)

        # ── Hitbox amarilla (solo personajes, no minijuego) ───────────────────
        if not mj_key and "interactable" in hitboxes:
            itr = hitboxes["interactable"]
            int_rect = pygame.Rect(
                spr_rect.left + int(scaled_w * itr["offset_x_ratio"]),
                spr_rect.top  + int(scaled_h * itr["offset_y_ratio"]),
                max(4, int(scaled_w * itr["w_ratio"])),
                max(4, int(scaled_h * itr["h_ratio"])),
            )
            iw2 = 3 if active_hb == "interactable" else 2
            pygame.draw.rect(screen, C_YELLOW, int_rect, iw2)
            pygame.draw.line(screen, C_YELLOW, (spr_rect.left, int_rect.top),    (spr_rect.right, int_rect.top), 1)
            pygame.draw.line(screen, C_YELLOW, (spr_rect.left, int_rect.bottom), (spr_rect.right, int_rect.bottom), 1)

        # ── Panel info ────────────────────────────────────────────────────────
        INFO_X = PREV_X + PREV_AREA_W + 42
        INFO_Y = PREV_Y - 14
        INFO_W = sw - INFO_X - 20
        pygame.draw.rect(screen, C_PANEL,  (INFO_X, INFO_Y, INFO_W, 500), border_radius=10)
        pygame.draw.rect(screen, C_BORDER, (INFO_X, INFO_Y, INFO_W, 500), 2, border_radius=10)

        active_label = "ROJA (colision)" if active_hb == "collision" else "AMARILLA (interactuable)"
        ahb = hitboxes[active_hb]
        px_w = max(4, int(scaled_w * ahb["w_ratio"]))
        px_h = max(4, int(scaled_h * ahb["h_ratio"]))
        actual_w = max(1, int(iw_raw * scale))
        actual_h = max(1, int(ih_raw * scale))

        if mj_key:
            info_lines = [
                f"Asset: {mj_key.upper()}",
                f"",
                f"Scale: {scale:.3f}   (Q/E)",
                f"  → sprite en juego: {actual_w}x{actual_h}px",
                f"",
                f"HITBOX ROJA (colision):",
                f"  rx: {ahb['offset_x_ratio']:.4f}   LEFT/RIGHT",
                f"  ry: {ahb['offset_y_ratio']:.4f}   UP/DOWN",
                f"  rw: {ahb['w_ratio']:.4f}    A/D",
                f"  rh: {ahb['h_ratio']:.4f}    W/S",
                f"  px: {px_w} x {px_h}",
                f"",
                f"Sin hitbox amarilla para minijuego.",
                f"",
                f"ENTER guardar  R reset",
                f"Ctrl+Z/Y undo/redo  ESC salir",
            ]
        else:
            info_lines = [
                f"Scale: {scale:.3f}   (Q/E)",
                f"  → sprite: {actual_w}x{actual_h}px",
                f"",
                f"Editando: {active_label}  (I)",
                f"  rx: {ahb['offset_x_ratio']:.4f}   LEFT/RIGHT",
                f"  ry: {ahb['offset_y_ratio']:.4f}   UP/DOWN",
                f"  rw: {ahb['w_ratio']:.4f}    A/D",
                f"  rh: {ahb['h_ratio']:.4f}    W/S",
                f"  px: {px_w} x {px_h}",
                f"",
                f"ENTER guardar   R reset",
                f"Ctrl+Z/Y undo/redo   ESC salir",
                f"",
                f"Config: {os.path.basename(config_path)}",
            ]
        draw_text(screen, "\n".join(info_lines), INFO_X + 14, INFO_Y + 14, font)

        # Preview caminata (solo personajes)
        if walk_frames:
            ai = (pygame.time.get_ticks() // 140) % len(walk_frames)
            wf = walk_frames[ai]
            ww, wh = wf.get_size()
            ws2  = pygame.transform.smoothscale(wf, (max(1, int(ww * scale)), max(1, int(wh * scale))))
            wr   = ws2.get_rect(centerx=INFO_X + 80, y=INFO_Y + 310)
            screen.blit(ws2, wr.topleft)
            chb  = hitboxes["collision"]
            cr2  = pygame.Rect(
                wr.left + int(ws2.get_width() * chb["offset_x_ratio"]),
                wr.top  + int(ws2.get_height() * chb["offset_y_ratio"]),
                max(4, int(ws2.get_width() * chb["w_ratio"])),
                max(4, int(ws2.get_height() * chb["h_ratio"])),
            )
            pygame.draw.rect(screen, C_RED, cr2, 2)
            screen.blit(small_font.render("walk preview", True, C_SOFT), (INFO_X + 4, INFO_Y + 306))

        # Status bar
        if status_timer > 0:
            status_timer -= 1
            ss = font.render(status_msg, True, (120, 230, 120))
            screen.blit(ss, (PREV_X - 14, sh - 30))

        pygame.display.flip()
        clock.tick(60)


# ─── Punto de entrada ─────────────────────────────────────────────────────────

def main():
    pygame.init()
    base_dir     = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)

    screen = pygame.display.set_mode((1400, 860))
    pygame.display.set_caption("Editor de personaje — EmpatiaQuest")
    clock = pygame.time.Clock()

    if len(sys.argv) > 1:
        sprite_path = sys.argv[1]
        if not os.path.isabs(sprite_path):
            sprite_path = os.path.join(project_root, sprite_path)
        if os.path.exists(sprite_path):
            run_editor(screen, clock, sprite_path, project_root)
            pygame.quit()
            return

    while True:
        selected = run_selector(screen, clock, project_root)
        if selected is None:
            break
        run_editor(screen, clock, selected, project_root)

    pygame.quit()


if __name__ == "__main__":
    main()
