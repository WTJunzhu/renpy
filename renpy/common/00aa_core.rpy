# Ace Attorney Ren'Py — Core Module
# CourtRecord data classes, evidence/character/location definitions, JSON loaders.
# All AA-specific data structures are defined here.

init -998 python in _aa:

    import json
    import os

    import store
    from store import config, renpy

    # ─── Registries ───────────────────────────────────────────

    # Animation state definitions. Creators extend via aa_register_animation().
    animation_states = {
        "idle":      {"frames": 1, "loop": True},
        "talk":      {"frames": 2, "loop": True},
        "objection": {"frames": 1, "loop": False},
        "breakdown": {"frames": 4, "loop": False},
        "sweat":     {"frames": 1, "loop": False},
        "slam":      {"frames": 2, "loop": False},
        "think":     {"frames": 1, "loop": False},
        "shock":     {"frames": 1, "loop": False},
        "smile":     {"frames": 1, "loop": False},
        "angry":     {"frames": 1, "loop": False},
        "sad":       {"frames": 1, "loop": False},
    }

    # Beep sound presets. Creators extend via aa_register_beep_preset().
    beep_presets = {
        "defense":     "audio/sfx/beep_defense.ogg",
        "prosecution": "audio/sfx/beep_prosecution.ogg",
        "witness":     "audio/sfx/beep_witness.ogg",
        "judge":       "audio/sfx/beep_judge.ogg",
        "narrator":    "audio/sfx/beep_narrator.ogg",
    }

    default_beep = "defense"

    def register_animation(name, frames=1, loop=False):
        animation_states[name] = {"frames": frames, "loop": loop}

    def register_beep_preset(name, path):
        beep_presets[name] = path

    def set_default_beep(name):
        global default_beep
        default_beep = name

    # ─── Callback Hooks ──────────────────────────────────────────
    # Each is a plain Python function variable. Assign to replace default.

    def _noop(*args, **kwargs):
        pass

    # Default penalty implementation: deduct HP and check game over.
    def _default_penalty(amount):
        store._aa_health = max(0, store._aa_health - amount)
        if store._aa_health <= 0:
            on_game_over()

    def _default_game_over():
        # Show a basic game over. Creators should override with their own.
        renpy.call_screen("aa_game_over")

    on_wrong_present = _noop               # (evidence_id, testimony_index)
    on_penalty = _default_penalty           # (amount)
    on_game_over = _default_game_over       # ()
    on_evidence_added = _noop              # (evidence_id)
    on_hotspot_examined = _noop            # (hotspot_id)
    on_testimony_complete = _noop          # ()

    # ─── Data Classes ────────────────────────────────────────────

    RO = renpy.revertable.RevertableObject
    RD = renpy.revertable.RevertableDict
    RL = renpy.revertable.RevertableList

    class Evidence(RO):
        """
        A single piece of evidence in the court record.
        Unknown JSON fields are stored in self.extra for creator extensions.
        """

        def __init__(self, data):
            self.id = data["id"]
            self.name = data["name"]
            self.description = data["description"]
            self.icon = data["icon"]
            self.examined = False

            examine = data.get("examine_images", [])
            self.examine_images = RL(examine) if not isinstance(examine, RL) else examine

            self.updated_description = data.get("updated_description")
            self.updated_icon = data.get("updated_icon")
            self.combinable_with = data.get("combinable_with")
            self.combine_result = data.get("combine_result")

            tags = data.get("tags", [])
            self.tags = RL(tags) if not isinstance(tags, RL) else tags

            known = {
                "id", "name", "description", "icon", "examine_images",
                "updated_description", "updated_icon",
                "combinable_with", "combine_result", "tags",
            }
            self.extra = RD()
            for k, v in data.items():
                if k not in known:
                    self.extra[k] = v

        def get_description(self):
            return self.updated_description or self.description

        def get_icon(self):
            return self.updated_icon or self.icon

        def update(self, **kwargs):
            for k, v in kwargs.items():
                if hasattr(self, k):
                    setattr(self, k, v)
                else:
                    self.extra[k] = v

    class Profile(RO):
        """
        A character profile that can appear in the court record.
        """

        def __init__(self, data):
            self.id = data["id"]
            self.name = data["name"]
            self.color = data.get("color", "#ffffff")
            self.beep_sfx = data.get("beep_sfx")
            self.position = data.get("position", "center")

            self.sprites = RD()
            for state, path in data.get("sprites", {}).items():
                if isinstance(path, list):
                    self.sprites[state] = RL(path)
                else:
                    self.sprites[state] = RL([path])

            known = {"id", "name", "color", "beep_sfx", "sprites", "position"}
            self.extra = RD()
            for k, v in data.items():
                if k not in known:
                    self.extra[k] = v

        def get_beep_path(self):
            if not self.beep_sfx:
                return beep_presets.get(default_beep, "")
            if self.beep_sfx.startswith("preset:"):
                preset_name = self.beep_sfx[7:]
                return beep_presets.get(preset_name, "")
            return self.beep_sfx

        def get_sprite(self, state):
            return self.sprites.get(state, RL())

    class HotspotDef(RO):
        """Definition of an investigation hotspot (read-only reference data)."""

        def __init__(self, data):
            self.id = data["id"]
            self.name = data["name"]
            self.position = data.get("position", [0, 0])
            self.size = data.get("size", [100, 100])
            self.radius = data.get("radius", 100)

    class NPCDef(RO):
        """Definition of an NPC in a location (read-only reference data)."""

        def __init__(self, data):
            self.id = data["id"]
            self.name = data["name"]
            self.position = data.get("position", [0, 0])
            self.sprite = data.get("sprite", "")

            topics = data.get("topics", [])
            self.topics = RL(topics) if not isinstance(topics, RL) else topics

            reactions = data.get("evidence_reactions", {})
            self.evidence_reactions = RD(reactions)

    class ExitDef(RO):
        """Definition of an exit/transition point in a location."""

        def __init__(self, data):
            self.target = data["target"]
            self.name = data["name"]
            self.position = data.get("position", [0, 0])
            self.size = data.get("size", [100, 200])
            self.condition = data.get("condition")

    class LocationDef(RO):
        """Definition of an investigation location (read-only reference data)."""

        def __init__(self, data):
            self.id = data["id"]
            self.name = data["name"]
            self.background = data.get("background", "")
            self.bgm = data.get("bgm")

            self.hotspots = RD()
            for h in data.get("hotspots", []):
                hd = HotspotDef(h)
                self.hotspots[hd.id] = hd

            self.npcs = RD()
            for n in data.get("npcs", []):
                nd = NPCDef(n)
                self.npcs[nd.id] = nd

            self.exits = RL()
            for e in data.get("exits", []):
                self.exits.append(ExitDef(e))

    # ─── CourtRecord (central game state) ────────────────────────

    class CourtRecord(RO):
        """
        Central manager for all dynamic game state.
        Inherits RevertableObject — automatically participates in save/load/rollback.
        """

        def __init__(self):
            self.evidence = RD()
            self.profiles = RD()
            self.locations = RD()
            self.flags = RD()
            self.examined_hotspots = RD()
            self.talked_topics = RD()
            self.npc_evidence_presented = RD()

        # ── Evidence ──

        def add_evidence(self, evidence_id, evidence_data=None):
            if evidence_id in self.evidence:
                return
            if evidence_data is None:
                raise ValueError("Evidence '{}' not found in loaded data.".format(evidence_id))
            self.evidence[evidence_id] = Evidence(evidence_data)
            on_evidence_added(evidence_id)

        def remove_evidence(self, evidence_id):
            if evidence_id in self.evidence:
                del self.evidence[evidence_id]

        def has_evidence(self, evidence_id):
            return evidence_id in self.evidence

        def get_evidence(self, evidence_id):
            return self.evidence.get(evidence_id)

        def update_evidence(self, evidence_id, **kwargs):
            ev = self.evidence.get(evidence_id)
            if ev:
                ev.update(**kwargs)

        def all_evidence(self):
            return list(self.evidence.values())

        # ── Profiles ──

        def add_profile(self, profile_id, profile_data=None):
            if profile_id in self.profiles:
                return
            if profile_data is None:
                raise ValueError("Profile '{}' not found in loaded data.".format(profile_id))
            self.profiles[profile_id] = Profile(profile_data)

        def has_profile(self, profile_id):
            return profile_id in self.profiles

        def get_profile(self, profile_id):
            return self.profiles.get(profile_id)

        def all_profiles(self):
            return list(self.profiles.values())

        # ── Locations ──

        def register_location(self, loc_data):
            loc = LocationDef(loc_data)
            self.locations[loc.id] = loc

        def get_location(self, loc_id):
            return self.locations.get(loc_id)

        # ── Flags ──

        def set_flag(self, key, value=True):
            self.flags[key] = value

        def get_flag(self, key, default=None):
            return self.flags.get(key, default)

        def has_flag(self, key):
            return key in self.flags

        def del_flag(self, key):
            if key in self.flags:
                del self.flags[key]

        # ── Hotspot tracking ──

        def mark_examined(self, hotspot_id):
            self.examined_hotspots[hotspot_id] = True

        def is_examined(self, hotspot_id):
            return self.examined_hotspots.get(hotspot_id, False)

        # ── NPC interaction tracking ──

        def mark_topic_talked(self, npc_id, topic):
            self.talked_topics["{}:{}".format(npc_id, topic)] = True

        def is_topic_talked(self, npc_id, topic):
            return self.talked_topics.get("{}:{}".format(npc_id, topic), False)

        def mark_evidence_presented(self, npc_id, evidence_id):
            self.npc_evidence_presented["{}:{}".format(npc_id, evidence_id)] = True

        def is_evidence_presented(self, npc_id, evidence_id):
            return self.npc_evidence_presented.get("{}:{}".format(npc_id, evidence_id), False)

    # ─── JSON Loaders ────────────────────────────────────────────

    # In-memory cache of raw evidence/profile/location data from JSON.
    # Used by get_evidence statement to create Evidence objects on demand.
    _evidence_defs = {}
    _profile_defs = {}
    _location_defs = {}

    def _load_json(filepath):
        full_path = os.path.join(config.gamedir, filepath)
        with open(full_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_evidence(filepath):
        data = _load_json(filepath)
        for ev_data in data.get("evidence", []):
            ev_id = ev_data["id"]
            _evidence_defs[ev_id] = ev_data
            if ev_id not in store.court_record.evidence:
                store.court_record.evidence[ev_id] = Evidence(ev_data)

    def load_profiles(filepath):
        data = _load_json(filepath)
        for p_data in data.get("characters", []):
            p_id = p_data["id"]
            _profile_defs[p_id] = p_data
            if p_id not in store.court_record.profiles:
                store.court_record.profiles[p_id] = Profile(p_data)

    def load_locations(filepath):
        data = _load_json(filepath)
        for loc_data in data.get("locations", []):
            _location_defs[loc_data["id"]] = loc_data
            store.court_record.register_location(loc_data)

    def load_case(filepath):
        return _load_json(filepath)

    # ─── Scene Displayable (Investigation) ──────────────────────
    #
    # Renders a location background with interactive hotspots and
    # a player character. Handles mouse click-to-move and WASD/arrow
    # keyboard movement. Returns hotspot ID when player interacts.

    _hotspot_defs = {}

    class SceneDisplayable(renpy.display.core.Displayable):
        """
        Custom displayable for investigation scenes.
        Renders background, hotspots, and player character.
        Handles click-to-move (smooth animation) and keyboard
        movement (instant). Returns hotspot ID on interaction.
        """

        MOVE_SPEED = 12
        ANIM_DURATION = 0.4

        def __init__(self, location_id, hotspot_defs, **kwargs):
            super(SceneDisplayable, self).__init__(**kwargs)
            self.location_id = location_id
            self.hotspot_defs = hotspot_defs or {}
            self._char_bg = renpy.easy.displayable("solid", "#3388ffcc")
            self._hotspot_bg = {}
            self._label_cache = {}
            self._checkmark = None
            self._bg_displayable = None

        def _get_hotspot_bg(self, hid, examined):
            key = (hid, examined)
            if key not in self._hotspot_bg:
                color = "#ffffff44" if not examined else "#ffffff22"
                self._hotspot_bg[key] = renpy.easy.displayable("solid", color)
            return self._hotspot_bg[key]

        def _get_label(self, text):
            if text not in self._label_cache:
                self._label_cache[text] = renpy.text.text.Text(
                    text=text, size=16, color="#ffffffcc", xanchor=0.5,
                )
            return self._label_cache[text]

        def _get_checkmark(self):
            if self._checkmark is None:
                self._checkmark = renpy.text.text.Text(
                    text="✓", size=20, color="#00ff00", xanchor=0.5,
                )
            return self._checkmark

        def render(self, width, height, st, at):
            # Click-to-move animation: interpolate position
            anim_start = store._aa_investigation_anim_start
            if anim_start >= 0 and st > anim_start:
                elapsed = st - anim_start
                progress = min(1.0, elapsed / self.ANIM_DURATION)
                ease_progress = progress * (2 - progress)  # ease-out quad

                start_x = store._aa_investigation_anim_from_x
                start_y = store._aa_investigation_anim_from_y
                target_x = store._aa_investigation_target_x
                target_y = store._aa_investigation_target_y

                new_x = start_x + (target_x - start_x) * ease_progress
                new_y = start_y + (target_y - start_y) * ease_progress
                store._aa_investigation_player_x = new_x
                store._aa_investigation_player_y = new_y

                if progress >= 1.0:
                    store._aa_investigation_anim_start = -1

            # Request continuous redraws for animation + input
            renpy.display.render.redraw(self, 0.016)

            rv = renpy.Render(width, height)

            # Draw background
            loc = store.court_record.get_location(self.location_id)
            if loc and loc.background:
                if self._bg_displayable is None:
                    self._bg_displayable = renpy.easy.displayable(loc.background)
                bg_render = self._bg_displayable.render(width, height, st, at)
                rv.blit(bg_render, (0, 0))

            # Draw hotspots
            for hid, hdef in self.hotspot_defs.items():
                examined = store.court_record.is_examined(hid)
                hx, hy = hdef.get("x", 0), hdef.get("y", 0)
                hw, hh = hdef.get("size_w", 100), hdef.get("size_h", 100)

                rect = self._get_hotspot_bg(hid, examined)
                rect_render = rect.render(hw, hh, st, at)
                rv.blit(rect_render, (hx, hy))

                lbl = self._get_label(hdef.get("name", ""))
                lbl_render = lbl.render(hw, 30, st, at)
                rv.blit(lbl_render, (hx + hw // 2, hy - 25))

                if examined:
                    mark = self._get_checkmark()
                    mark_render = mark.render(30, 30, st, at)
                    rv.blit(mark_render, (hx + hw - 10, hy + 5))

            # Draw player character
            px = store._aa_investigation_player_x
            py = store._aa_investigation_player_y
            char_render = self._char_bg.render(40, 80, st, at)
            rv.blit(char_render, (px - 20, py - 80))

            return rv

        def event(self, ev, x, y, st):
            import renpy.pygame as pygame

            px = store._aa_investigation_player_x
            py = store._aa_investigation_player_y

            # Mouse click — move or interact
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for hid, hdef in self.hotspot_defs.items():
                    hx, hy = hdef.get("x", 0), hdef.get("y", 0)
                    hw, hh = hdef.get("size_w", 100), hdef.get("size_h", 100)
                    if hx <= x <= hx + hw and hy <= y <= hy + hh:
                        dist = ((px - (hx + hw // 2)) ** 2 +
                                (py - (hy + hh // 2)) ** 2) ** 0.5
                        radius = hdef.get("radius", 100)
                        if dist <= radius:
                            return hid
                        else:
                            # Click-to-move toward hotspot
                            store._aa_investigation_anim_from_x = px
                            store._aa_investigation_anim_from_y = py
                            store._aa_investigation_target_x = hx + hw // 2
                            store._aa_investigation_target_y = hy + hh // 2
                            store._aa_investigation_anim_start = st
                            renpy.display.render.redraw(self, 0)
                            return None
                # Click-to-move to empty area
                store._aa_investigation_anim_from_x = px
                store._aa_investigation_anim_from_y = py
                store._aa_investigation_target_x = x
                store._aa_investigation_target_y = y
                store._aa_investigation_anim_start = st
                renpy.display.render.redraw(self, 0)
                return None

            # Keyboard — movement + interaction
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_e, pygame.K_RETURN):
                    for hid, hdef in self.hotspot_defs.items():
                        hx, hy = hdef.get("x", 0), hdef.get("y", 0)
                        hw, hh = hdef.get("size_w", 100), hdef.get("size_h", 100)
                        dist = ((px - (hx + hw // 2)) ** 2 +
                                (py - (hy + hh // 2)) ** 2) ** 0.5
                        radius = hdef.get("radius", 100)
                        if dist <= radius:
                            return hid
                    return None
                elif ev.key == pygame.K_ESCAPE:
                    return "__exit__"

                dx, dy = 0, 0
                if ev.key in (pygame.K_w, pygame.K_UP):
                    dy = -self.MOVE_SPEED
                elif ev.key in (pygame.K_s, pygame.K_DOWN):
                    dy = self.MOVE_SPEED
                elif ev.key in (pygame.K_a, pygame.K_LEFT):
                    dx = -self.MOVE_SPEED
                elif ev.key in (pygame.K_d, pygame.K_RIGHT):
                    dx = self.MOVE_SPEED

                if dx != 0 or dy != 0:
                    # Cancel click-to-move animation
                    store._aa_investigation_anim_start = -1
                    new_x = max(0, min(1920, px + dx))
                    new_y = max(0, min(1080, py + dy))
                    store._aa_investigation_player_x = new_x
                    store._aa_investigation_player_y = new_y
                    renpy.display.render.redraw(self, 0)
                    return None

            return None

        def visit(self):
            return []


# ─── Store-level defaults (rollback-aware) ───────────────────────

default court_record = _aa.CourtRecord()

# Convenience aliases at store level — let creators write
#   court_record.add_evidence(...)
#   aa_load_evidence("aa/evidence.json")
# without needing the _aa prefix.

init -996 python:
    aa_load_evidence = _aa.load_evidence
    aa_load_profiles = _aa.load_profiles
    aa_load_locations = _aa.load_locations
    aa_load_case = _aa.load_case
    aa_register_animation = _aa.register_animation
    aa_register_beep_preset = _aa.register_beep_preset
    aa_set_default_beep = _aa.set_default_beep
    aa_make_character = _aa_text.make_aa_character
