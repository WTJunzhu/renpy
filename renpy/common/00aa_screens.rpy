# Ace Attorney Ren'Py — Courtroom UI Screens
# Health bar, testimony panel, evidence selection, press/present buttons.
# All screens use placeholder visuals — creators override by defining
# a screen with the same name.

# ─── Health Bar ──────────────────────────────────────────────────
#
# Variables used:
#   _aa_health      — current HP (int)
#   _aa_max_health  — maximum HP (int)

default _aa_health = 5
default _aa_max_health = 5

screen aa_health_bar():
    zorder 100

    $ hp = _aa_health
    $ max_hp = _aa_max_health

    hbox:
        xalign 0.5
        ypos 10
        spacing 4

        for i in range(max_hp):
            frame:
                xsize 40
                ysize 20
                if i < hp:
                    background "#2ecc40"  # green
                else:
                    background "#555555"  # dark gray
                text str(i + 1):
                    xalign 0.5
                    yalign 0.5
                    size 12
                    color "#fff"


# ─── Testimony Panel ─────────────────────────────────────────────
#
# Variables used:
#   _aa_testimony_stmts   — list of statement strings (or None)
#   _aa_testimony_index   — current statement index
#   _aa_testimony_title   — title string ("证言中" etc.)
#   _aa_testimony_active  — bool, True when in testimony/cross-examination

default _aa_testimony_active = False

screen aa_testimony_panel():
    zorder 90

    if _aa_testimony_active and _aa_testimony_stmts is not None:

        $ stmts = _aa_testimony_stmts
        $ idx = _aa_testimony_index
        $ title = _aa_testimony_title

        # Background panel
        frame:
            xfill True
            ysize 200
            yalign 1.0
            background "#000000cc"
            xpadding 20
            ypadding 15

            vbox:
                xfill True
                spacing 8

                # Title bar
                hbox:
                    xfill True
                    text title:
                        size 20
                        color "#ffcc00"
                        xalign 0.5

                # Progress dots
                hbox:
                    xalign 0.5
                    spacing 6
                    for i in range(len(stmts)):
                        frame:
                            xsize 12
                            ysize 12
                            if i == idx:
                                background "#ffcc00"  # gold — current
                            else:
                                background "#666666"  # gray — other

                # Current statement text
                if 0 <= idx < len(stmts):
                    text stmts[idx]:
                        xfill True
                        size 24
                        color "#ffffff"
                        text_align 0.5

                # Navigation hint
                hbox:
                    xfill True
                    text "← → 切换证言 | Z 威慑 | X 举证":
                        size 14
                        color "#888888"
                        xalign 0.5


# ─── Evidence Selection Panel ────────────────────────────────────
#
# Variables used:
#   court_record.evidence — dict of Evidence objects
#   _aa_evidence_panel_open — bool, True when panel is visible
#
# Returns selected evidence ID via store._aa_selected_evidence
# or None if cancelled.

default _aa_evidence_panel_open = False
default _aa_selected_evidence = None

screen aa_evidence_panel():
    zorder 200
    modal True

    if _aa_evidence_panel_open:

        # Semi-transparent backdrop
        frame:
            xfill True
            yfill True
            background "#000000dd"
            xpadding 40
            ypadding 30

            vbox:
                xfill True
                yfill True
                spacing 10

                # Title
                text "法庭记录" size 28 color "#ffcc00" xalign 0.5

                null height 10

                # Evidence grid
                grid 4 3:
                    xfill True
                    yfill True
                    spacing 10

                    for ev in list(court_record.evidence.values()):
                        button:
                            action [
                                SetVariable("_aa_selected_evidence", ev.id),
                                Hide("aa_evidence_panel"),
                            ]
                            xfill True
                            ysize 100
                            background "#333333"
                            hover_background "#555555"

                            vbox:
                                xfill True
                                spacing 4
                                text ev.name size 16 color "#ffffff"
                                text ev.get_description()[:40] size 12 color "#aaaaaa"

                    # Fill empty grid slots
                    for i in range(max(0, 12 - len(court_record.evidence))):
                        null

                null height 10

                # Cancel button
                textbutton "取消 (ESC)":
                    xalign 0.5
                    action [
                        SetVariable("_aa_selected_evidence", None),
                        Hide("aa_evidence_panel"),
                    ]

    # Cancel via ESC
    key "game_menu" action [
        SetVariable("_aa_selected_evidence", None),
        Hide("aa_evidence_panel"),
    ]


# ─── Press / Present Button Bar ──────────────────────────────────
#
# Shown during cross-examination. Provides Z (press) and X (present) buttons.
#
# Variables used:
#   _aa_testimony_active — bool
#   _aa_can_press — bool, whether press is available on current stmt
#   _aa_can_present — bool, whether present is available

default _aa_can_press = True
default _aa_can_present = True

screen aa_press_present_bar():
    zorder 95

    if _aa_testimony_active:

        hbox:
            xalign 0.5
            ypos 220  # just above testimony panel
            spacing 20

            # Press button (Z)
            textbutton "威慑 (Z)":
                action NullAction()
                text_size 22
                if _aa_can_press:
                    text_color "#4488ff"
                else:
                    text_color "#444444"

            # Present button (X)
            textbutton "举证 (X)":
                action NullAction()
                text_size 22
                if _aa_can_present:
                    text_color "#44cc44"
                else:
                    text_color "#444444"


# ─── Key Bindings ────────────────────────────────────────────────
#
# Global key handling for AA courtroom mode.

screen aa_courtroom_keys():
    zorder 50

    if _aa_testimony_active and _aa_testimony_stmts is not None:

        $ stmts = _aa_testimony_stmts
        $ idx = _aa_testimony_index

        # Arrow keys — navigate testimony
        key "K_LEFT" action SetVariable("_aa_testimony_index", max(0, idx - 1))
        key "K_RIGHT" action SetVariable("_aa_testimony_index", min(len(stmts) - 1, idx + 1))

        # C — toggle evidence panel
        key "K_c" action [
            ToggleVariable("_aa_evidence_panel_open"),
            SetVariable("_aa_selected_evidence", None),
        ]

    # ESC — close evidence panel if open
    if _aa_evidence_panel_open:
        key "K_ESCAPE" action [
            SetVariable("_aa_evidence_panel_open", False),
            SetVariable("_aa_selected_evidence", None),
        ]


# ─── Game Over Screen ────────────────────────────────────────────

screen aa_game_over():
    modal True
    zorder 999

    frame:
        xfill True
        yfill True
        background "#000000ee"

        vbox:
            xalign 0.5
            yalign 0.5
            spacing 30

            text "有罪" size 80 color "#ff0000" xalign 0.5
            text "Game Over" size 30 color "#ffffff" xalign 0.5

            textbutton "Load" action ShowMenu("load") xalign 0.5
            textbutton "Title" action MainMenu() xalign 0.5


# ─── Map Screen ──────────────────────────────────────────────────
#
# Shows available investigation locations. Used during investigation
# phase for location navigation.
#
# Variables used:
#   _aa_available_locations — list of location dicts with id, name, locked
#
# Returns selected location ID, or None if cancelled.

default _aa_available_locations = []

screen aa_map():
    zorder 180
    modal True

    frame:
        xfill True
        yfill True
        background "#000000dd"
        xpadding 40
        ypadding 30

        vbox:
            xfill True
            yfill True
            spacing 10

            text "地图" size 28 color "#ffcc00" xalign 0.5

            null height 10

            vbox:
                xalign 0.5
                spacing 8

                for loc in _aa_available_locations:
                    if loc.get("locked", False):
                        textbutton loc["name"]:
                            xalign 0.5
                            text_size 22
                            text_color "#555555"
                            action NullAction()
                    else:
                        textbutton loc["name"]:
                            xalign 0.5
                            text_size 22
                            text_color "#ffffff"
                            action Return(loc["id"])

            null height 20

            textbutton "取消 (ESC)":
                xalign 0.5
                text_size 18
                text_color "#888888"
                action Return(None)

    key "K_ESCAPE" action Return(None)
