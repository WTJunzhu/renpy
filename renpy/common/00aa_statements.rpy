# Ace Attorney Ren'Py — Statement Registration Framework
# Defines all AA custom statements with blocking interaction logic.
#
# IMPORTANT: Statement registration happens in `python early` blocks
# which execute at PARSE TIME. Runtime logic (execute/next handlers)
# lives in `init python` blocks which execute later.

# ─── Parse-Time: Statement Registration ──────────────────────────
# This block runs during script parsing. It registers all custom
# statement names so Ren'Py's parser recognizes them.

python early hide:

    # NOTE: Do NOT `import renpy` here. In the store namespace, `renpy`
    # is already `renpy.exports` which has `register_statement`.
    # Importing would overwrite it with the raw module that lacks it.

    # ─── Registration Helper ─────────────────────────────────────

    def register(name, parse=None, execute=None, next=None, block=False,
                 lint=None, predict=None, **kwargs):
        renpy.register_statement(
            name,
            parse=parse,
            execute=execute,
            next=next,
            block=block,
            lint=lint,
            predict=predict,
            **kwargs
        )

    # ─── Common Parse Helpers ────────────────────────────────────

    def parse_string(lexer):
        return lexer.string()

    def parse_integer(lexer):
        return lexer.integer()

    def parse_name(lexer):
        return lexer.name()

    def require(lexer, parse_func, label):
        rv = parse_func(lexer)
        if rv is None:
            raise Exception("Expected {}.".format(label))
        return rv

    # ─── penalty ─────────────────────────────────────────────────
    # Syntax: penalty <amount>

    def parse_penalty(lexer):
        amount = parse_integer(lexer)
        return {"amount": amount if amount is not None else 1}

    register("penalty", parse=parse_penalty)

    # ─── get_evidence ────────────────────────────────────────────
    # Syntax: get_evidence <evidence_id>

    def parse_get_evidence(lexer):
        ev_id = parse_name(lexer)
        if ev_id is None:
            ev_id = require(lexer, parse_string, "evidence id")
        return {"evidence_id": ev_id}

    register("get_evidence", parse=parse_get_evidence)

    # ─── remove_evidence ─────────────────────────────────────────
    # Syntax: remove_evidence <evidence_id>

    def parse_remove_evidence(lexer):
        ev_id = parse_name(lexer)
        if ev_id is None:
            ev_id = require(lexer, parse_string, "evidence id")
        return {"evidence_id": ev_id}

    register("remove_evidence", parse=parse_remove_evidence)

    # ─── set_flag ────────────────────────────────────────────────
    # Syntax: set_flag <key> [to <value>]

    def parse_set_flag(lexer):
        key = parse_name(lexer)
        if key is None:
            raise Exception("Expected a flag name.")
        value = True
        if lexer.keyword("to"):
            v = parse_integer(lexer)
            if v is not None:
                value = v
            else:
                vs = parse_string(lexer)
                if vs is not None:
                    value = vs
                else:
                    vn = parse_name(lexer)
                    if vn == "true":
                        value = True
                    elif vn == "false":
                        value = False
                    elif vn is not None:
                        value = vn
        return {"key": key, "value": value}

    register("set_flag", parse=parse_set_flag)

    # ─── add_stmt ────────────────────────────────────────────────
    # Syntax: add_stmt "text"

    def parse_add_stmt(lexer):
        text = require(lexer, parse_string, "statement text")
        return {"text": text}

    register("add_stmt", parse=parse_add_stmt)

    # ─── stmt ────────────────────────────────────────────────────
    # Syntax: stmt "text"

    def parse_stmt(lexer):
        text = require(lexer, parse_string, "statement text")
        return {"text": text}

    register("stmt", parse=parse_stmt)

    # ─── end_testimony ───────────────────────────────────────────
    # Syntax: end_testimony

    def parse_end_testimony(lexer):
        return {}

    register("end_testimony", parse=parse_end_testimony)

    # ─── begin_testimony ─────────────────────────────────────────
    # Syntax: begin_testimony "title" [by <character_id>]

    def parse_begin_testimony(lexer):
        title = require(lexer, parse_string, "testimony title")
        by_char = None
        if lexer.keyword("by"):
            by_char = require(lexer, parse_name, "character id")
        return {"title": title, "by": by_char}

    register("begin_testimony", parse=parse_begin_testimony, block="script")

    # ─── cross_examination ───────────────────────────────────────
    # Syntax: cross_examination "title"

    def parse_cross_examination(lexer):
        title = require(lexer, parse_string, "cross-examination title")
        return {"title": title}

    register("cross_examination", parse=parse_cross_examination, block="script")

    # ─── press ───────────────────────────────────────────────────
    # Syntax: press <target>

    def parse_press(lexer):
        target = parse_integer(lexer)
        if target is None:
            kw = parse_name(lexer)
            if kw == "current":
                target = "current"
            else:
                raise Exception("press requires an integer index or 'current'.")
        return {"target": target}

    register("press", parse=parse_press, block="script")

    # ─── present ─────────────────────────────────────────────────
    # Syntax: present <target> using <evidence_id> [or <evidence_id2>...]

    def parse_present(lexer):
        # Two syntaxes:
        #   present <target> using <evidence_id> [or ...]   (testimony)
        #   present <evidence_id>                           (talk/NPC)
        target = parse_integer(lexer)
        if target is None:
            kw = parse_name(lexer)
            if kw == "current":
                target = "current"
            elif kw is not None and lexer.keyword("using"):
                # kw was actually an evidence id in talk mode
                # Rewind: treat kw as first evidence id, target = "current"
                correct_ids = [kw]
                while lexer.keyword("or"):
                    correct_ids.append(require(lexer, parse_name, "evidence id"))
                return {"target": "current", "correct_ids": correct_ids, "talk_mode": True}
            elif kw is not None:
                # No 'using' — talk mode: kw is the evidence id
                return {"target": "current", "correct_ids": [kw], "talk_mode": True}
            else:
                raise Exception("present requires a target or evidence id.")
        require(lexer, lambda l: l.keyword("using"), "'using' keyword")
        correct_ids = [require(lexer, parse_name, "evidence id")]
        while lexer.keyword("or"):
            correct_ids.append(require(lexer, parse_name, "evidence id"))
        return {"target": target, "correct_ids": correct_ids}

    register("present", parse=parse_present, block="script")

    # ─── investigate ─────────────────────────────────────────────
    # Syntax: investigate "scene_name" at <location_id>

    def parse_investigate(lexer):
        scene_name = require(lexer, parse_string, "scene name")
        loc_id = None
        if lexer.keyword("at"):
            loc_id = require(lexer, parse_name, "location id")
        return {"scene_name": scene_name, "location_id": loc_id}

    register("investigate", parse=parse_investigate, block="script")

    # ─── hotspot ─────────────────────────────────────────────────
    # Syntax: hotspot "name" at (x, y) size (w, h) [radius r]

    def parse_hotspot(lexer):
        name = require(lexer, parse_string, "hotspot name")
        require(lexer, lambda l: l.keyword("at"), "'at' keyword")
        x = require(lexer, parse_integer, "x coordinate")
        y = require(lexer, parse_integer, "y coordinate")
        size_w, size_h = 100, 100
        if lexer.keyword("size"):
            size_w = require(lexer, parse_integer, "width")
            size_h = require(lexer, parse_integer, "height")
        radius = 100
        if lexer.keyword("radius"):
            radius = require(lexer, parse_integer, "radius")
        hotspot_id = name.lower().replace(" ", "_")
        return {
            "hotspot_id": hotspot_id,
            "name": name,
            "x": x, "y": y,
            "size_w": size_w, "size_h": size_h,
            "radius": radius,
        }

    register("hotspot", parse=parse_hotspot, block="script")

    # ─── examine ─────────────────────────────────────────────────
    # Syntax: examine <hotspot_id>

    def parse_examine(lexer):
        hotspot_id = require(lexer, parse_name, "hotspot id")
        return {"hotspot_id": hotspot_id}

    register("examine", parse=parse_examine, block="script")

    # ─── end_investigate ─────────────────────────────────────────
    # Syntax: end_investigate

    def parse_end_investigate(lexer):
        return {}

    register("end_investigate", parse=parse_end_investigate)

    # ─── talk ────────────────────────────────────────────────────
    # Syntax: talk <npc_id>

    def parse_talk(lexer):
        npc_id = require(lexer, parse_name, "NPC id")
        return {"npc_id": npc_id}

    register("talk", parse=parse_talk, block="script")

    # ─── topic ───────────────────────────────────────────────────
    # Syntax: topic "name"

    def parse_topic(lexer):
        topic_name = require(lexer, parse_string, "topic name")
        return {"topic_name": topic_name}

    register("topic", parse=parse_topic, block="script")

    # ─── move ────────────────────────────────────────────────────
    # Syntax: move <location_id> [if <condition>]

    def parse_move(lexer):
        loc_id = require(lexer, parse_name, "location id")
        condition = None
        if lexer.keyword("if"):
            condition = require(lexer, parse_name, "condition flag")
        return {"location_id": loc_id, "condition": condition}

    register("move", parse=parse_move)


# ─── Runtime: Execute/Next Handlers ──────────────────────────────
# This block runs at init time. It sets up the _aa reference and
# defines all execute/next handler functions, then re-registers
# statements with the full handler set.

init -997 python in _aa_stmt:

    import renpy
    import store

    _aa = renpy.store._aa

    # ─── Helper: re-register with execute/next ───────────────────

    def _reregister(name, parse=None, execute=None, next=None,
                    block=False, **kwargs):
        renpy.register_statement(
            name,
            parse=parse,
            execute=execute,
            next=next,
            block=block,
            **kwargs
        )

    # ─── Common Parse Helpers (redefined for runtime use) ────────

    def parse_string(lexer):
        return lexer.string()

    def parse_integer(lexer):
        return lexer.integer()

    def parse_name(lexer):
        return lexer.name()

    def require(lexer, parse_func, label):
        rv = parse_func(lexer)
        if rv is None:
            raise Exception("Expected {}.".format(label))
        return rv

    # ─── Node inspection helpers ─────────────────────────────────

    def _is_statement(node, name):
        node_name = getattr(node, 'name', None)
        if node_name:
            return name in node_name
        line = getattr(node, 'line', None) or getattr(node, 'py_code', '')
        if line:
            return line.strip().startswith(name)
        return False

    def _get_node_parsed(node):
        return getattr(node, 'parsed', None)

    def _target_matches(target, idx):
        if target == "current":
            return True
        if isinstance(target, int):
            return target == idx
        return False

    # ─── Interaction Loop ────────────────────────────────────────

    def _interaction_loop():
        while True:
            store._aa_testimony_active = True
            renpy.show_screen("aa_testimony_panel")
            renpy.show_screen("aa_press_present_bar")
            renpy.show_screen("aa_courtroom_keys")

            action = renpy.call_screen("aa_testimony_interact")
            renpy.hide_screen("aa_testimony_interact")

            if action is None:
                continue

            if action.startswith("present:"):
                idx = int(action.split(":")[1])
                correct_ids = store._aa_present_correct_ids

                store._aa_evidence_panel_open = True
                store._aa_selected_evidence = None
                renpy.show_screen("aa_evidence_panel")
                selected = renpy.call_screen("aa_evidence_select")
                store._aa_evidence_panel_open = False
                renpy.hide_screen("aa_evidence_panel")

                if selected is None:
                    continue

                if selected in correct_ids:
                    store._aa_present_result = True
                    return "present:{}".format(idx)
                else:
                    store._aa_present_result = False
                    _aa.on_wrong_present(selected, idx)
                    if store._aa_health <= 0:
                        return "game_over"
                    continue

            elif action.startswith("press:"):
                idx = int(action.split(":")[1])
                return "press:{}".format(idx)

    # ─── penalty ─────────────────────────────────────────────────

    def execute_penalty(parsed):
        _aa.on_penalty(parsed["amount"])
        renpy.restart_interaction()

    _reregister("penalty", parse=parse_penalty, execute=execute_penalty)

    # ─── get_evidence ────────────────────────────────────────────

    def execute_get_evidence(parsed):
        ev_id = parsed["evidence_id"]
        ev_data = _aa._evidence_defs.get(ev_id)
        if ev_data is not None:
            store.court_record.add_evidence(ev_id, ev_data)
        else:
            raise Exception("Evidence '{}' not defined.".format(ev_id))
        renpy.restart_interaction()

    _reregister("get_evidence", parse=parse_get_evidence,
                execute=execute_get_evidence)

    # ─── remove_evidence ─────────────────────────────────────────

    def execute_remove_evidence(parsed):
        store.court_record.remove_evidence(parsed["evidence_id"])
        renpy.restart_interaction()

    _reregister("remove_evidence", parse=parse_remove_evidence,
                execute=execute_remove_evidence)

    # ─── set_flag ────────────────────────────────────────────────

    def execute_set_flag(parsed):
        store.court_record.set_flag(parsed["key"], parsed["value"])
        renpy.restart_interaction()

    _reregister("set_flag", parse=parse_set_flag, execute=execute_set_flag)

    # ─── add_stmt ────────────────────────────────────────────────

    def execute_add_stmt(parsed):
        if store._aa_testimony_stmts is not None:
            store._aa_testimony_stmts.append(parsed["text"])
        renpy.restart_interaction()

    _reregister("add_stmt", parse=parse_add_stmt, execute=execute_add_stmt)

    # ─── stmt ────────────────────────────────────────────────────

    def execute_stmt(parsed):
        if store._aa_testimony_stmts is not None:
            store._aa_testimony_stmts.append(parsed["text"])
            store._aa_testimony_index = len(store._aa_testimony_stmts) - 1
        renpy.restart_interaction()

    _reregister("stmt", parse=parse_stmt, execute=execute_stmt)

    # ─── end_testimony ───────────────────────────────────────────

    def execute_end_testimony(parsed):
        store._aa_testimony_stmts = None
        store._aa_testimony_index = 0
        store._aa_testimony_title = ""
        store._aa_testimony_active = False
        _aa.on_testimony_complete()
        renpy.restart_interaction()

    _reregister("end_testimony", parse=parse_end_testimony,
                execute=execute_end_testimony)

    # ─── begin_testimony ─────────────────────────────────────────

    def execute_begin_testimony(parsed):
        store._aa_testimony_title = parsed["title"]
        store._aa_testimony_stmts = []
        store._aa_testimony_index = 0
        store._aa_testimony_active = True
        store._aa_press_handlers = {}
        store._aa_present_handlers = {}
        renpy.restart_interaction()

    def next_begin_testimony(parsed, block):
        if block is None:
            return None

        for node in block:
            renpy.execute(node)

        while True:
            result = _interaction_loop()

            if result == "game_over":
                _aa.on_game_over()
                return None

            if result.startswith("present:"):
                idx = int(result.split(":")[1])
                for node in block:
                    if _is_statement(node, "present"):
                        node_parsed = _get_node_parsed(node)
                        if node_parsed and _target_matches(node_parsed.get("target"), idx):
                            if hasattr(node, 'block') and node.block:
                                for child in node.block:
                                    renpy.execute(child)
                            break
                store._aa_testimony_active = False
                renpy.restart_interaction()
                return None

            elif result.startswith("press:"):
                idx = int(result.split(":")[1])
                for node in block:
                    if _is_statement(node, "press"):
                        node_parsed = _get_node_parsed(node)
                        if node_parsed and _target_matches(node_parsed.get("target"), idx):
                            if hasattr(node, 'block') and node.block:
                                for child in node.block:
                                    renpy.execute(child)
                            break
                continue

        return None

    _reregister("begin_testimony", parse=parse_begin_testimony,
                execute=execute_begin_testimony, next=next_begin_testimony,
                block="script")

    # ─── cross_examination ───────────────────────────────────────

    def execute_cross_examination(parsed):
        execute_begin_testimony(parsed)

    def next_cross_examination(parsed, block):
        return next_begin_testimony(parsed, block)

    _reregister("cross_examination", parse=parse_cross_examination,
                execute=execute_cross_examination,
                next=next_cross_examination, block="script")

    # ─── press ───────────────────────────────────────────────────

    def execute_press(parsed):
        store._aa_press_target = parsed["target"]
        renpy.restart_interaction()

    def next_press(parsed, block):
        if not store._aa_testimony_active:
            return block
        return None

    _reregister("press", parse=parse_press, execute=execute_press,
                next=next_press, block="script")

    # ─── present ─────────────────────────────────────────────────

    def execute_present(parsed):
        store._aa_present_target = parsed["target"]
        store._aa_present_correct_ids = parsed["correct_ids"]
        renpy.restart_interaction()

    def next_present(parsed, block):
        if store._aa_testimony_active:
            return None

        correct_ids = parsed["correct_ids"]
        while True:
            store._aa_evidence_panel_open = True
            store._aa_selected_evidence = None
            renpy.show_screen("aa_evidence_panel")
            selected = renpy.call_screen("aa_evidence_select")
            store._aa_evidence_panel_open = False
            renpy.hide_screen("aa_evidence_panel")

            if selected is None:
                continue

            if selected in correct_ids:
                return block
            else:
                _aa.on_wrong_present(selected, 0)
                if store._aa_health <= 0:
                    _aa.on_game_over()
                    return None
                continue

    _reregister("present", parse=parse_present, execute=execute_present,
                next=next_present, block="script")

    # ─── investigate ─────────────────────────────────────────────

    def execute_investigate(parsed):
        store._aa_investigation_active = True
        store._aa_investigation_location = parsed["location_id"]
        store._aa_examine_handlers = {}
        renpy.restart_interaction()

    def next_investigate(parsed, block):
        if block is None:
            return None

        _aa._hotspot_defs = {}
        for node in block:
            if _is_statement(node, "hotspot"):
                node_parsed = _get_node_parsed(node)
                if node_parsed:
                    hid = node_parsed.get("hotspot_id")
                    if hid:
                        _aa._hotspot_defs[hid] = node_parsed
                        if hasattr(node, 'block') and node.block:
                            for child in node.block:
                                if _is_statement(child, "examine"):
                                    ex_parsed = _get_node_parsed(child)
                                    if ex_parsed:
                                        ex_hid = ex_parsed.get("hotspot_id")
                                        if ex_hid:
                                            store._aa_examine_handlers[ex_hid] = child

        while True:
            store._aa_investigation_active = True
            hotspot_id = renpy.call_screen(
                "aa_investigation_scene",
                location_id=parsed["location_id"],
                hotspot_defs=_aa._hotspot_defs,
            )

            if hotspot_id == "__exit__":
                break

            if hotspot_id is None:
                continue

            store.court_record.mark_examined(hotspot_id)
            _aa.on_hotspot_examined(hotspot_id)

            examine_node = store._aa_examine_handlers.get(hotspot_id)
            if examine_node is not None and hasattr(examine_node, 'block') and examine_node.block:
                for child in examine_node.block:
                    renpy.execute(child)

            renpy.restart_interaction()

        store._aa_investigation_active = False
        store._aa_investigation_location = None
        _aa._hotspot_defs = {}
        store._aa_examine_handlers = {}
        renpy.restart_interaction()
        return None

    _reregister("investigate", parse=parse_investigate,
                execute=execute_investigate, next=next_investigate,
                block="script")

    # ─── hotspot ─────────────────────────────────────────────────

    def execute_hotspot(parsed):
        pass

    def next_hotspot(parsed, block):
        return None

    _reregister("hotspot", parse=parse_hotspot, execute=execute_hotspot,
                next=next_hotspot, block="script")

    # ─── examine ─────────────────────────────────────────────────

    def execute_examine(parsed):
        pass

    def next_examine(parsed, block):
        return None

    _reregister("examine", parse=parse_examine, execute=execute_examine,
                next=next_examine, block="script")

    # ─── end_investigate ─────────────────────────────────────────

    def execute_end_investigate(parsed):
        store._aa_investigation_active = False
        store._aa_investigation_location = None
        renpy.restart_interaction()

    _reregister("end_investigate", parse=parse_end_investigate,
                execute=execute_end_investigate)

    # ─── talk ────────────────────────────────────────────────────

    def execute_talk(parsed):
        store._aa_talk_npc = parsed["npc_id"]
        store._aa_talk_topic_handlers = {}
        store._aa_talk_present_handlers = {}
        renpy.restart_interaction()

    def next_talk(parsed, block):
        if block is None:
            return None

        npc_id = parsed["npc_id"]

        topic_names = []
        for node in block:
            if _is_statement(node, "topic"):
                node_parsed = _get_node_parsed(node)
                if node_parsed:
                    tname = node_parsed.get("topic_name")
                    if tname:
                        store._aa_talk_topic_handlers[tname] = node
                        topic_names.append(tname)
            elif _is_statement(node, "present"):
                node_parsed = _get_node_parsed(node)
                if node_parsed:
                    ev_id = node_parsed.get("evidence_id")
                    if ev_id:
                        store._aa_talk_present_handlers[ev_id] = node

        while True:
            available = []
            for tname in topic_names:
                if not store.court_record.is_topic_talked(npc_id, tname):
                    available.append(tname)

            choice = renpy.call_screen(
                "aa_talk_menu",
                npc_id=npc_id,
                topics=available,
                has_present=len(store._aa_talk_present_handlers) > 0,
            )

            if choice == "__exit__":
                break

            elif choice == "__present__":
                selected = renpy.call_screen("aa_evidence_select")
                if selected is not None:
                    present_node = store._aa_talk_present_handlers.get(selected)
                    if present_node is not None:
                        store.court_record.mark_evidence_presented(npc_id, selected)
                        if hasattr(present_node, 'block') and present_node.block:
                            for child in present_node.block:
                                renpy.execute(child)
                    else:
                        renpy.say(None, "这个不太相关吧……")
                    renpy.restart_interaction()

            elif choice in store._aa_talk_topic_handlers:
                store.court_record.mark_topic_talked(npc_id, choice)
                topic_node = store._aa_talk_topic_handlers[choice]
                if hasattr(topic_node, 'block') and topic_node.block:
                    for child in topic_node.block:
                        renpy.execute(child)
                renpy.restart_interaction()

        store._aa_talk_npc = None
        store._aa_talk_topic_handlers = {}
        store._aa_talk_present_handlers = {}
        renpy.restart_interaction()
        return None

    _reregister("talk", parse=parse_talk, execute=execute_talk,
                next=next_talk, block="script")

    # ─── topic ───────────────────────────────────────────────────

    def execute_topic(parsed):
        pass

    def next_topic(parsed, block):
        return None

    _reregister("topic", parse=parse_topic, execute=execute_topic,
                next=next_topic, block="script")

    # ─── move ────────────────────────────────────────────────────

    def execute_move(parsed):
        loc_id = parsed["location_id"]
        condition = parsed.get("condition")

        if condition and not store.court_record.has_flag(condition):
            renpy.say(None, "现在没有必要去那里。")
            renpy.restart_interaction()
            return

        loc = store.court_record.get_location(loc_id)
        if loc is None:
            raise Exception("Location '{}' not defined.".format(loc_id))

        store._aa_investigation_location = loc_id

        if loc.bgm:
            try:
                renpy.music.play(loc.bgm, channel="music")
            except Exception:
                pass

        renpy.restart_interaction()

    _reregister("move", parse=parse_move, execute=execute_move)


# ─── Blocking Screens ────────────────────────────────────────────

screen aa_testimony_interact():
    modal False
    zorder 80

    $ stmts = _aa_testimony_stmts or []
    $ idx = _aa_testimony_index

    if len(stmts) > 0:
        key "K_z" action Return("press:{}".format(idx))
    if len(stmts) > 0:
        key "K_x" action Return("present:{}".format(idx))

    if idx > 0:
        key "K_LEFT" action [
            SetVariable("_aa_testimony_index", idx - 1),
            Function(_play_ding),
        ]
    if idx < len(stmts) - 1:
        key "K_RIGHT" action [
            SetVariable("_aa_testimony_index", idx + 1),
            Function(_play_ding),
        ]

    key "K_SPACE" action NullAction()
    key "K_RETURN" action NullAction()

screen aa_evidence_select():
    modal True
    zorder 200

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

            text "法庭记录" size 28 color "#ffcc00" xalign 0.5
            null height 10

            grid 4 3:
                xfill True
                yfill True
                spacing 10

                for ev in list(court_record.evidence.values()):
                    button:
                        action Return(ev.id)
                        xfill True
                        ysize 100
                        background "#333333"
                        hover_background "#555555"
                        vbox:
                            xfill True
                            spacing 4
                            text ev.name size 16 color "#ffffff"
                            text ev.get_description()[:40] size 12 color "#aaaaaa"

                for i in range(max(0, 12 - len(court_record.evidence))):
                    null

            null height 10
            textbutton "取消 (ESC)" xalign 0.5 action Return(None)

    key "K_ESCAPE" action Return(None)


screen aa_investigation_scene(location_id, hotspot_defs):
    modal False
    zorder 80

    $ scene = _aa.SceneDisplayable(location_id, hotspot_defs)
    add scene

    timer 0.016 action Function(renpy.restart_interaction) repeat True

    frame:
        xalign 0.5
        ypos 10
        background "#000000aa"
        xpadding 15
        ypadding 5
        text "WASD/方向键移动 | E/点击交互 | ESC退出":
            size 14
            color "#888888"

    key "K_ESCAPE" action Return("__exit__")


screen aa_talk_menu(npc_id, topics, has_present):
    modal True
    zorder 150

    frame:
        xfill True
        yfill True
        background "#000000dd"
        xpadding 60
        ypadding 40

        vbox:
            xalign 0.5
            yalign 0.5
            spacing 15

            $ profile = court_record.get_profile(npc_id)
            $ display_name = profile.name if profile else npc_id

            text "[display_name]" size 28 color "#ffcc00" xalign 0.5

            null height 10

            if len(topics) > 0:
                for tname in topics:
                    textbutton tname:
                        xalign 0.5
                        text_size 22
                        action Return(tname)
            else:
                text "（没有更多话题）" size 18 color "#888888" xalign 0.5

            null height 10

            if has_present:
                textbutton "出示证物":
                    xalign 0.5
                    text_size 22
                    text_color "#44cc44"
                    action Return("__present__")

            textbutton "结束对话":
                xalign 0.5
                text_size 18
                text_color "#888888"
                action Return("__exit__")

    key "K_ESCAPE" action Return("__exit__")


# ─── Helper ──────────────────────────────────────────────────────

init -997 python in _aa_stmt:
    def _play_ding():
        try:
            renpy.audio.music.play("audio/sfx/ding.ogg", channel="aa_beep", loop=False)
        except Exception:
            pass


# ─── Store variables ─────────────────────────────────────────────

default _aa_testimony_stmts = None
default _aa_testimony_index = 0
default _aa_testimony_title = ""
default _aa_testimony_active = False
default _aa_press_target = None
default _aa_present_target = None
default _aa_present_correct_ids = []
default _aa_present_result = False
default _aa_press_handlers = {}
default _aa_present_handlers = {}
default _aa_investigation_active = False
default _aa_investigation_location = None
default _aa_examine_handlers = {}
default _aa_investigation_player_x = 960
default _aa_investigation_player_y = 800
default _aa_investigation_target_x = 960
default _aa_investigation_target_y = 800
default _aa_investigation_anim_start = -1
default _aa_investigation_anim_from_x = 960
default _aa_investigation_anim_from_y = 800
default _aa_talk_npc = None
default _aa_talk_topic_handlers = {}
default _aa_talk_present_handlers = {}
