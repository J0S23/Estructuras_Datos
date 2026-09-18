"""
Editor visual de alineación — EmpatiaQuest
==========================================
PANTALLA 1 — Elige el objeto interactuable y el sprite/animación.
PANTALLA 2 — Alinea, escala y guarda con Enter.

Controles en pantalla de SELECCIÓN
────────────────────────────────────
  ↑ ↓          Navegar lista activa
  PgUp/PgDn    Saltar 10 items
  Tab          Cambiar entre panel Objetos ↔ Sprites
  Enter        Confirmar ítem seleccionado / Abrir alineador
  Rueda mouse  Scroll en la lista bajo el cursor
  ESC          Salir

Controles en pantalla de ALINEACIÓN
────────────────────────────────────
  Arrastar mouse  Mover sprite
  ← → ↑ ↓        Mover sprite 1 px  (Shift = 5 px, Ctrl = 10 px)
  Z / X           Escala horizontal ±5 %
  C / V           Escala vertical   ±5 %
  Rueda mouse     Zoom de la vista
  Shift+Rueda     Escala horizontal ±5 %
  Ctrl+Rueda      Escala vertical   ±5 %
  PgUp / PgDn     DESK_TOP_FRAC ±0.01  (donde empieza la mesa en el sprite)
  T               Vista: ambos / solo objeto / solo sprite
  A               Opacidad del sprite
  Enter           Guardar offsets
  R               Resetear a valores por defecto
  ESC             Volver a selección
"""

import pygame
import os
import sys
import re
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# ── Constantes globales ───────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1280, 720
WORLD_W_REF = int(1920 * 1.35)   # 2592
WORLD_H_REF = int(1080 * 1.35)   # 1458

DEFAULT_OFFSET_X  =  0.0
DEFAULT_OFFSET_Y  =  0.0
DEFAULT_DESK_FRAC =  0.35
DEFAULT_SCALE_W   =  1.0
DEFAULT_SCALE_H   =  1.0

OFFSETS_FILE = os.path.join(ROOT, "Alineaciones", "alineacion_offsets.json")

# El par que además sincroniza a config.py:
CONFIG_PAIR_OBJ = "Pupitre-Salón1.png"
CONFIG_PAIR_SPR = "seated.png"


# ── Escaneo de datos ──────────────────────────────────────────────────────────

def scan_objects():
    """Lee todos los JSON de Objetos/ y devuelve objetos únicos."""
    objdir = os.path.join(ROOT, "Objetos")
    seen = {}
    if not os.path.isdir(objdir):
        # Alcalde Digital no tiene carpeta Objetos/ (es de EmpatiaQuest).
        # Sin objetos este editor no tiene nada que alinear.
        return []
    for fname in sorted(os.listdir(objdir)):
        if not fname.endswith(".json") or fname.startswith("_"):
            continue
        try:
            with open(os.path.join(objdir, fname), "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        for obj in data.get("objects", []):
            name = obj.get("name", "")
            if not name or name in seen:
                continue
            cd = obj.get("crop")
            crop = (cd["x"], cd["y"], cd["w"], cd["h"]) if cd else None
            seen[name] = {
                "name":   name,
                "rw":     obj.get("w", 0.1),
                "rh":     obj.get("h", 0.1),
                "crop":   crop,
                "source": fname.replace("_objetos.json", ""),
            }
    return sorted(seen.values(), key=lambda o: o["name"].lower())


def scan_sprites():
    """Devuelve todos los PNG bajo Imagenes/Personajes/ e Imagenes/Interactuables/."""
    results = []
    for subdir in ("Personajes", "Interactuables"):
        base = os.path.join(ROOT, "Imagenes", subdir)
        if not os.path.isdir(base):
            continue
        for dirpath, _, files in os.walk(base):
            for f in sorted(files):
                if f.lower().endswith(".png"):
                    full = os.path.join(dirpath, f)
                    rel = os.path.relpath(full, os.path.join(ROOT, "Imagenes")).replace("\\", "/")
                    results.append({"label": rel, "path": full, "name": f})
    return results


# ── Config I/O ────────────────────────────────────────────────────────────────

def load_offsets():
    try:
        with open(OFFSETS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_offsets_file(data):
    os.makedirs(os.path.dirname(OFFSETS_FILE), exist_ok=True)
    with open(OFFSETS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def pair_key(obj_name, spr_name):
    return f"{obj_name}|{spr_name}"


def sync_to_config_py(offset_x, offset_y, desk_frac):
    """Escribe SEATED_OFFSET_X/Y y SEATED_DESK_TOP_FRAC en config.py."""
    path = os.path.join(ROOT, "config.py")
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return

    def rep(text, name, value):
        fmt = str(int(value)) if float(value) == int(float(value)) else f"{value:.4f}"
        return re.sub(rf'({re.escape(name)}\s*=\s*)[^\s#\n]+', rf'\g<1>{fmt}', text)

    content = rep(content, "SEATED_OFFSET_X",      offset_x)
    content = rep(content, "SEATED_OFFSET_Y",      offset_y)
    content = rep(content, "SEATED_DESK_TOP_FRAC", desk_frac)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ── Utilidades de imagen ──────────────────────────────────────────────────────

def find_image_file(name):
    for dirpath, _, files in os.walk(os.path.join(ROOT, "Imagenes")):
        if name in files:
            return os.path.join(dirpath, name)
    return None


def load_image(path, crop=None):
    try:
        img = pygame.image.load(path).convert_alpha()
    except Exception:
        surf = pygame.Surface((80, 60), pygame.SRCALPHA)
        surf.fill((200, 80, 80, 200))
        return surf
    if crop:
        cx, cy, cw, ch = crop
        iw, ih = img.get_size()
        r = pygame.Rect(int(cx * iw), int(cy * ih),
                        max(1, int(cw * iw)), max(1, int(ch * ih)))
        img = img.subsurface(r).copy()
    return img


# ── Utilidades de render ──────────────────────────────────────────────────────

def draw_checker(surf, rect, size=14):
    for row in range(rect.y, rect.bottom, size):
        for col in range(rect.x, rect.right, size):
            c = (190, 190, 190) if ((row // size + col // size) % 2 == 0) else (145, 145, 145)
            pygame.draw.rect(surf, c,
                             (col, row, min(size, rect.right - col), min(size, rect.bottom - row)))


def blit_text(surf, text, x, y, font, color, right_align=False, center=False):
    s = font.render(text, True, color)
    if right_align:
        x -= s.get_width()
    elif center:
        x -= s.get_width() // 2
    surf.blit(s, (x, y))
    return s.get_width()


# ── PANTALLA 1: Selección ─────────────────────────────────────────────────────

def run_selection(screen, objects, sprites, all_offsets, font_sm, font_md):
    """
    Muestra dos listas. Retorna (obj_entry, spr_entry) o None si cierra.
    Flujo: confirma objeto con Enter → confirma sprite con Enter → lanza alineador.
    """
    clock = pygame.time.Clock()

    PANEL_W  = 530
    LIST_H   = SCREEN_H - 200   # altura de la lista (deja espacio para thumb + barra)
    ITEM_H   = 26
    THUMB_H  = 90
    OBJ_X    = 20
    SPR_X    = SCREEN_W - PANEL_W - 20
    LIST_Y   = 70

    obj_sel   = 0;  obj_scroll = 0
    spr_sel   = 0;  spr_scroll = 0
    focus     = 0   # 0 = objetos, 1 = sprites
    confirmed_obj = None   # obj_entry confirmado

    # Filtro de búsqueda (typing)
    filter_obj = ""
    filter_spr = ""

    thumb_cache = {}

    def get_filtered(items, flt, key_fn):
        if not flt:
            return items, list(range(len(items)))
        low = flt.lower()
        idxs = [i for i, it in enumerate(items) if low in key_fn(it).lower()]
        return [items[i] for i in idxs], idxs

    def get_thumb(path, crop=None):
        key = (path, str(crop))
        if key not in thumb_cache:
            try:
                img = load_image(path, crop)
                iw, ih = img.get_size()
                scale  = min(PANEL_W / max(1, iw), THUMB_H / max(1, ih), 1.0)
                nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
                thumb_cache[key] = pygame.transform.smoothscale(img, (nw, nh))
            except Exception:
                thumb_cache[key] = None
        return thumb_cache[key]

    def visible_count():
        return max(1, LIST_H // ITEM_H)

    def draw_panel(items_f, sel_f, scroll, px, focused, title):
        """items_f = lista ya filtrada."""
        vis = visible_count()
        # Cabecera
        col = (255, 220, 50) if focused else (140, 140, 165)
        blit_text(screen, title, px, LIST_Y - 26, font_md, col)

        # Área de lista
        lrect = pygame.Rect(px, LIST_Y, PANEL_W, LIST_H)
        pygame.draw.rect(screen, (20, 22, 36), lrect)
        border_col = (255, 220, 50) if focused else (50, 54, 80)
        pygame.draw.rect(screen, border_col, lrect, 1)

        screen.set_clip(lrect)
        for i in range(vis + 1):
            idx = scroll + i
            if idx >= len(items_f):
                break
            iy = LIST_Y + i * ITEM_H
            if iy >= LIST_Y + LIST_H:
                break
            is_sel = (idx == sel_f)
            bg = (65, 58, 110) if is_sel else ((32, 35, 52) if i % 2 == 0 else (26, 28, 44))
            pygame.draw.rect(screen, bg, (px, iy, PANEL_W - 8, ITEM_H))
            text_col = (255, 240, 100) if is_sel else (190, 200, 220)
            label = items_f[idx]["name"] if "source" in items_f[idx] else items_f[idx]["label"]
            # fuente de nombre del objeto: name + (source)
            if "source" in items_f[idx]:
                label = f"{items_f[idx]['name']}  [{items_f[idx]['source']}]"
            # Truncar
            max_w = PANEL_W - 18
            rendered = font_sm.render(label, True, text_col)
            if rendered.get_width() > max_w:
                while len(label) > 4 and font_sm.size(label + "…")[0] > max_w:
                    label = label[:-1]
                label += "…"
                rendered = font_sm.render(label, True, text_col)
            screen.blit(rendered, (px + 6, iy + (ITEM_H - rendered.get_height()) // 2))
        screen.set_clip(None)

        # Scrollbar
        if len(items_f) > vis:
            sb_h  = LIST_H
            tb_h  = max(18, sb_h * vis // max(1, len(items_f)))
            tb_y  = LIST_Y + (sb_h - tb_h) * scroll // max(1, len(items_f) - vis)
            pygame.draw.rect(screen, (40, 44, 68), (px + PANEL_W - 8, LIST_Y, 8, sb_h))
            scroll_col = (150, 160, 220) if focused else (80, 88, 130)
            pygame.draw.rect(screen, scroll_col, (px + PANEL_W - 8, tb_y, 8, tb_h))

        # Thumbnail del ítem seleccionado
        if 0 <= sel_f < len(items_f):
            it = items_f[sel_f]
            thr = pygame.Rect(px, LIST_Y + LIST_H + 6, PANEL_W, THUMB_H)
            draw_checker(screen, thr, 12)
            if "source" in it:  # es objeto
                img_path = find_image_file(it["name"])
                th = get_thumb(img_path, it.get("crop")) if img_path else None
            else:
                th = get_thumb(it["path"])
            if th:
                bx = thr.x + (thr.w - th.get_width()) // 2
                by = thr.y + (thr.h - th.get_height()) // 2
                screen.blit(th, (bx, by))
            pygame.draw.rect(screen, border_col, thr, 1)

    def clamp_scroll(sel, scroll, items_count):
        vis = visible_count()
        scroll = max(0, min(scroll, max(0, items_count - vis)))
        if sel < scroll:
            scroll = sel
        elif sel >= scroll + vis:
            scroll = sel - vis + 1
        return scroll

    while True:
        clock.tick(60)

        objs_f, _ = get_filtered(objects, filter_obj, lambda o: o["name"])
        sprs_f, _ = get_filtered(sprites, filter_spr, lambda s: s["label"])

        obj_sel    = max(0, min(obj_sel, len(objs_f) - 1)) if objs_f else 0
        spr_sel    = max(0, min(spr_sel, len(sprs_f) - 1)) if sprs_f else 0
        obj_scroll = clamp_scroll(obj_sel, obj_scroll, len(objs_f))
        spr_scroll = clamp_scroll(spr_sel, spr_scroll, len(sprs_f))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            elif event.type == pygame.MOUSEWHEEL:
                mx = pygame.mouse.get_pos()[0]
                vis = visible_count()
                if OBJ_X <= mx < OBJ_X + PANEL_W:
                    obj_scroll = max(0, min(max(0, len(objs_f) - vis), obj_scroll - event.y))
                elif SPR_X <= mx < SPR_X + PANEL_W:
                    spr_scroll = max(0, min(max(0, len(sprs_f) - vis), spr_scroll - event.y))

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                for panel_x, is_obj in ((OBJ_X, True), (SPR_X, False)):
                    if panel_x <= mx < panel_x + PANEL_W and LIST_Y <= my < LIST_Y + LIST_H:
                        focus = 0 if is_obj else 1
                        idx = (obj_scroll if is_obj else spr_scroll) + (my - LIST_Y) // ITEM_H
                        items_f = objs_f if is_obj else sprs_f
                        if 0 <= idx < len(items_f):
                            if is_obj:
                                if obj_sel == idx:
                                    confirmed_obj = objs_f[obj_sel]; focus = 1
                                else:
                                    obj_sel = idx
                            else:
                                if spr_sel == idx and confirmed_obj is not None:
                                    return (confirmed_obj, sprs_f[spr_sel])
                                else:
                                    spr_sel = idx

            elif event.type == pygame.KEYDOWN:
                k = event.key
                vis = visible_count()

                if k == pygame.K_ESCAPE:
                    return None

                elif k == pygame.K_TAB:
                    focus = 1 - focus

                elif k == pygame.K_BACKSPACE:
                    if focus == 0:
                        filter_obj = filter_obj[:-1]; obj_sel = 0; obj_scroll = 0
                    else:
                        filter_spr = filter_spr[:-1]; spr_sel = 0; spr_scroll = 0

                elif k == pygame.K_UP:
                    if focus == 0: obj_sel = max(0, obj_sel - 1)
                    else:          spr_sel = max(0, spr_sel - 1)

                elif k == pygame.K_DOWN:
                    if focus == 0: obj_sel = min(len(objs_f) - 1, obj_sel + 1)
                    else:          spr_sel = min(len(sprs_f) - 1, spr_sel + 1)

                elif k == pygame.K_PAGEUP:
                    if focus == 0: obj_sel = max(0, obj_sel - vis)
                    else:          spr_sel = max(0, spr_sel - vis)

                elif k == pygame.K_PAGEDOWN:
                    if focus == 0: obj_sel = min(len(objs_f) - 1, obj_sel + vis)
                    else:          spr_sel = min(len(sprs_f) - 1, spr_sel + vis)

                elif k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if focus == 0:
                        if objs_f:
                            confirmed_obj = objs_f[obj_sel]; focus = 1
                    else:
                        if confirmed_obj and sprs_f:
                            return (confirmed_obj, sprs_f[spr_sel])

                else:
                    # Búsqueda por escritura
                    ch = event.unicode
                    if ch and ch.isprintable():
                        if focus == 0:
                            filter_obj += ch; obj_sel = 0; obj_scroll = 0
                        else:
                            filter_spr += ch; spr_sel = 0; spr_scroll = 0

        # ── Render selección ──────────────────────────────────────────────────
        screen.fill((14, 15, 26))

        blit_text(screen, "EDITOR DE ALINEACIÓN  —  Selecciona objeto y sprite",
                  SCREEN_W // 2, 14, font_md, (255, 220, 50), center=True)

        draw_panel(objs_f, obj_sel, obj_scroll, OBJ_X,  focus == 0, "OBJETOS INTERACTUABLES")
        draw_panel(sprs_f, spr_sel, spr_scroll, SPR_X,  focus == 1, "SPRITES / ANIMACIONES")

        # Estado de confirmación
        if confirmed_obj:
            msg = f"✓ {confirmed_obj['name']}  →  selecciona sprite y presiona Enter"
            blit_text(screen, msg, SCREEN_W // 2, LIST_Y + LIST_H + THUMB_H + 14,
                      font_sm, (80, 235, 105), center=True)
        else:
            blit_text(screen, "Selecciona un objeto y presiona Enter",
                      SCREEN_W // 2, LIST_Y + LIST_H + THUMB_H + 14,
                      font_sm, (160, 160, 190), center=True)

        # Filtros activos
        if filter_obj:
            blit_text(screen, f"Filtro: {filter_obj}_", OBJ_X, LIST_Y + LIST_H + THUMB_H + 34,
                      font_sm, (255, 180, 60))
        if filter_spr:
            blit_text(screen, f"Filtro: {filter_spr}_", SPR_X, LIST_Y + LIST_H + THUMB_H + 34,
                      font_sm, (255, 180, 60))

        # Barra inferior
        bar_y = SCREEN_H - 34
        pygame.draw.rect(screen, (18, 20, 34), (0, bar_y - 4, SCREEN_W, 38))
        pygame.draw.line(screen, (45, 50, 75), (0, bar_y - 4), (SCREEN_W, bar_y - 4), 1)
        blit_text(screen,
                  "↑↓ navegar   Tab cambiar panel   Escribe para filtrar   Enter confirmar   Doble-clic confirmar   ESC salir",
                  SCREEN_W // 2, bar_y + 6, font_sm, (130, 135, 160), center=True)

        pygame.display.flip()


# ── PANTALLA 2: Alineación ────────────────────────────────────────────────────

INFO_H = 155

def run_alignment(screen, obj_entry, spr_entry, all_offsets, font_sm, font_md):
    """Alineador visual. Enter guarda. ESC vuelve a selección."""
    clock   = pygame.time.Clock()
    PREV_H  = SCREEN_H - INFO_H
    prev_rc = pygame.Rect(0, 0, SCREEN_W, PREV_H)

    pw_base = max(8, int(WORLD_W_REF * obj_entry["rw"]))
    ph_base = max(8, int(WORLD_H_REF * obj_entry["rh"]))

    obj_path = find_image_file(obj_entry["name"])
    obj_img  = load_image(obj_path, obj_entry.get("crop")) if obj_path else None
    if obj_img is None:
        obj_img = pygame.Surface((pw_base, ph_base), pygame.SRCALPHA)
        obj_img.fill((160, 110, 60, 200))
    spr_img  = load_image(spr_entry["path"])

    # Cargar offsets guardados para este par
    key  = pair_key(obj_entry["name"], spr_entry["name"])
    prev = all_offsets.get(key, {})
    offset_x  = float(prev.get("offset_x",  DEFAULT_OFFSET_X))
    offset_y  = float(prev.get("offset_y",  DEFAULT_OFFSET_Y))
    desk_frac = float(prev.get("desk_frac", DEFAULT_DESK_FRAC))
    scale_w   = float(prev.get("scale_w",   DEFAULT_SCALE_W))
    scale_h   = float(prev.get("scale_h",   DEFAULT_SCALE_H))

    zoom        = 2.0
    view_mode   = 0       # 0=ambos 1=solo obj 2=solo spr
    spr_alpha   = 255
    ALPHAS      = (64, 128, 192, 255)
    alpha_idx   = 3
    saved_flash = 0
    dragging    = False
    drag_start  = (0, 0)
    drag_ox0    = drag_oy0 = 0.0

    CHKSZ = 16

    def do_save():
        nonlocal saved_flash
        entry = {
            "offset_x":  round(offset_x,  3),
            "offset_y":  round(offset_y,  3),
            "desk_frac": round(desk_frac, 4),
            "scale_w":   round(scale_w,   3),
            "scale_h":   round(scale_h,   3),
        }
        all_offsets[key] = entry
        save_offsets_file(all_offsets)
        # Sincronizar config.py para el par pupitre+seated
        if obj_entry["name"] == CONFIG_PAIR_OBJ and spr_entry["name"] == CONFIG_PAIR_SPR:
            sync_to_config_py(offset_x, offset_y, desk_frac)
        saved_flash = 2200

    while True:
        dt = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return all_offsets

            elif event.type == pygame.MOUSEWHEEL:
                mods = pygame.key.get_mods()
                if mods & pygame.KMOD_SHIFT:
                    scale_w = round(max(0.05, min(10.0, scale_w + event.y * 0.05)), 3)
                elif mods & pygame.KMOD_CTRL:
                    scale_h = round(max(0.05, min(10.0, scale_h + event.y * 0.05)), 3)
                else:
                    zoom = max(0.4, min(8.0, zoom + event.y * 0.25))

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and prev_rc.collidepoint(event.pos):
                    dragging = True
                    drag_start = event.pos
                    drag_ox0, drag_oy0 = offset_x, offset_y
                elif event.button == 4:   # rueda arriba (pygame < 2)
                    zoom = min(8.0, zoom + 0.25)
                elif event.button == 5:   # rueda abajo
                    zoom = max(0.4, zoom - 0.25)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    dragging = False

            elif event.type == pygame.MOUSEMOTION and dragging:
                dx = event.pos[0] - drag_start[0]
                dy = event.pos[1] - drag_start[1]
                offset_x = drag_ox0 + dx / zoom
                offset_y = drag_oy0 + dy / zoom

            elif event.type == pygame.KEYDOWN:
                mods  = pygame.key.get_mods()
                shift = bool(mods & pygame.KMOD_SHIFT)
                ctrl  = bool(mods & pygame.KMOD_CTRL)
                step  = 10 if ctrl else (5 if shift else 1)
                k = event.key

                if k == pygame.K_ESCAPE:
                    return all_offsets
                elif k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    do_save()
                elif k == pygame.K_r:
                    offset_x, offset_y = DEFAULT_OFFSET_X, DEFAULT_OFFSET_Y
                    desk_frac = DEFAULT_DESK_FRAC
                    scale_w, scale_h  = DEFAULT_SCALE_W, DEFAULT_SCALE_H
                elif k == pygame.K_t:
                    view_mode = (view_mode + 1) % 3
                elif k == pygame.K_a:
                    alpha_idx = (alpha_idx + 1) % len(ALPHAS)
                    spr_alpha = ALPHAS[alpha_idx]
                elif k in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                    zoom = min(8.0, zoom + 0.25)
                elif k in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    zoom = max(0.4, zoom - 0.25)
                elif k == pygame.K_LEFT:
                    offset_x -= step
                elif k == pygame.K_RIGHT:
                    offset_x += step
                elif k == pygame.K_UP:
                    offset_y -= step
                elif k == pygame.K_DOWN:
                    offset_y += step
                elif k == pygame.K_PAGEUP:
                    desk_frac = round(min(0.90, desk_frac + 0.01), 4)
                elif k == pygame.K_PAGEDOWN:
                    desk_frac = round(max(0.05, desk_frac - 0.01), 4)
                # Escala horizontal: Z/X
                elif k == pygame.K_z:
                    scale_w = round(max(0.05, scale_w - 0.05), 3)
                elif k == pygame.K_x:
                    scale_w = round(min(10.0, scale_w + 0.05), 3)
                # Escala vertical: C/V
                elif k == pygame.K_c:
                    scale_h = round(max(0.05, scale_h - 0.05), 3)
                elif k == pygame.K_v:
                    scale_h = round(min(10.0, scale_h + 0.05), 3)

        # ── Geometría ─────────────────────────────────────────────────────────
        frac  = max(0.05, min(0.90, desk_frac))
        obj_w = max(1, int(pw_base * zoom))
        obj_h = max(1, int(ph_base * zoom))

        # Tamaño base del sprite (basado en ph_base y DESK_TOP_FRAC, igual que el juego)
        base_size = ph_base / (1.0 - frac)
        sp_w = max(1, int(base_size * zoom * scale_w))
        sp_h = max(1, int(base_size * zoom * scale_h))

        obj_x = prev_rc.centerx - obj_w // 2
        obj_y = prev_rc.centery - obj_h // 2
        sp_x  = obj_x + obj_w // 2 - sp_w // 2 + int(offset_x * zoom)
        sp_y  = obj_y - int(frac * sp_h)         + int(offset_y * zoom)

        # ── Render ────────────────────────────────────────────────────────────
        screen.fill((30, 32, 42))

        # Tablero de ajedrez
        for row in range(0, PREV_H, CHKSZ):
            for col in range(0, SCREEN_W, CHKSZ):
                c = (185, 185, 185) if ((row // CHKSZ + col // CHKSZ) % 2 == 0) else (148, 148, 148)
                pygame.draw.rect(screen, c, (col, row, CHKSZ, CHKSZ))

        show_obj = view_mode in (0, 1)
        show_spr = view_mode in (0, 2)

        if show_obj:
            screen.blit(pygame.transform.smoothscale(obj_img, (obj_w, obj_h)), (obj_x, obj_y))

        if show_spr:
            spr_scaled = pygame.transform.smoothscale(spr_img, (sp_w, sp_h))
            if spr_alpha < 255:
                spr_scaled.set_alpha(spr_alpha)
            screen.blit(spr_scaled, (sp_x, sp_y))

        # Contornos
        pygame.draw.rect(screen, (255, 220, 50), (obj_x, obj_y, obj_w, obj_h), 1)
        pygame.draw.rect(screen, (80, 180, 255), (sp_x,  sp_y,  sp_w, sp_h), 1)
        # Línea roja = tope de la mesa en el sprite
        dl_y = sp_y + int(frac * sp_h)
        pygame.draw.line(screen, (255, 55, 55), (sp_x, dl_y), (sp_x + sp_w, dl_y), 2)
        # Cruz central del objeto
        cx, cy = obj_x + obj_w // 2, obj_y + obj_h // 2
        pygame.draw.line(screen, (255, 255, 255), (cx - 12, cy), (cx + 12, cy), 1)
        pygame.draw.line(screen, (255, 255, 255), (cx, cy - 12), (cx, cy + 12), 1)

        # Etiqueta par (top-left) y vista (top-right)
        pair_lbl = f"{obj_entry['name']}  +  {spr_entry['name']}"
        blit_text(screen, pair_lbl, 8, 6, font_sm, (180, 200, 255))
        VIEW_LABELS = ["Ambos", "Solo objeto", "Solo sprite"]
        view_lbl = font_sm.render(f"Vista: {VIEW_LABELS[view_mode]}  (T)", True, (200, 200, 160))
        screen.blit(view_lbl, (SCREEN_W - view_lbl.get_width() - 8, 6))

        # ── Panel de info ─────────────────────────────────────────────────────
        pygame.draw.rect(screen, (16, 18, 30), (0, PREV_H, SCREEN_W, INFO_H))
        pygame.draw.line(screen, (55, 60, 90), (0, PREV_H), (SCREEN_W, PREV_H), 2)

        C1, C2, C3 = 14, 420, 840
        R = [PREV_H + 10 + i * 27 for i in range(5)]

        # Columna izquierda: valores actuales
        blit_text(screen, f"OFFSET X  : {offset_x:+.1f} px",     C1, R[0], font_sm, (210, 215, 235))
        blit_text(screen, f"OFFSET Y  : {offset_y:+.1f} px",     C1, R[1], font_sm, (210, 215, 235))
        blit_text(screen, f"DESK_FRAC : {desk_frac:.3f}",         C1, R[2], font_sm, (210, 215, 235))
        blit_text(screen, f"ESCALA W  : ×{scale_w:.2f}",          C1, R[3], font_sm, (210, 215, 235))
        blit_text(screen, f"ESCALA H  : ×{scale_h:.2f}",          C1, R[4], font_sm, (210, 215, 235))

        # Columna central: controles
        dim = (148, 155, 180)
        blit_text(screen, "← → ↑ ↓  mover sprite  (Shift×5 Ctrl×10)",    C2, R[0], font_sm, dim)
        blit_text(screen, "Rueda / + −   zoom de vista",                   C2, R[1], font_sm, dim)
        blit_text(screen, "Shift+Rueda / Z X   escala horizontal",         C2, R[2], font_sm, dim)
        blit_text(screen, "Ctrl+Rueda  / C V   escala vertical",           C2, R[3], font_sm, dim)
        blit_text(screen, "PgUp PgDn   línea de mesa  |  A opacidad",      C2, R[4], font_sm, dim)

        # Columna derecha: acciones
        if saved_flash > 0:
            blit_text(screen, "✓  Guardado!", C3, R[1], font_md, (75, 235, 110))
            saved_flash -= dt
        else:
            blit_text(screen, "Enter  Guardar",    C3, R[1], font_sm, (110, 210, 120))
        blit_text(screen, "R      Resetear",        C3, R[2], font_sm, (195, 148, 148))
        blit_text(screen, "T      Alternar vista",  C3, R[3], font_sm, (175, 175, 135))
        blit_text(screen, "ESC    ← Selección",     C3, R[4], font_sm, (175, 135, 135))

        # Tamaños en pantalla
        blit_text(screen,
                  f"Obj {obj_w}×{obj_h} px   Spr {sp_w}×{sp_h} px   Zoom ×{zoom:.2f}",
                  C3, R[0], font_sm, (110, 120, 145))

        pygame.display.flip()

    return all_offsets


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    pygame.key.set_repeat(170, 26)
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Editor de Alineación — EmpatiaQuest")

    font_sm = pygame.font.SysFont("Consolas", 15)
    font_md = pygame.font.SysFont("Consolas", 18, bold=True)

    objects     = scan_objects()
    sprites     = scan_sprites()
    all_offsets = load_offsets()

    if not objects or not sprites:
        print("Este editor sirve para alinear un personaje sentado con un mueble")
        print("(pupitres de EmpatiaQuest). Alcalde Digital no tiene esa mecánica:")
        print("no hay carpeta Objetos/ con muebles ni sprites sentados que alinear.")
        print("Ver Editores/MANUAL.md — este editor no se usa en este proyecto.")
        pygame.quit()
        return

    while True:
        result = run_selection(screen, objects, sprites, all_offsets, font_sm, font_md)
        if result is None:
            break
        obj_entry, spr_entry = result
        all_offsets = run_alignment(screen, obj_entry, spr_entry, all_offsets, font_sm, font_md)

    pygame.quit()


if __name__ == "__main__":
    main()
