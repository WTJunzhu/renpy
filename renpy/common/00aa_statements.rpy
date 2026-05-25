# Ace Attorney Ren'Py — Statement Registration Framework
# Defines all AA custom statements with blocking interaction logic.

init -997 python in _aa_stmt:

    import renpy
    import store

    _aa = renpy.store._aa

    # ─── Statement Registration Helper ───────────────────────────

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

    # ─── Interaction Loop (core of cross-examination) ────────────
    #
    # Shows testimony UI, waits for player action (Z/X/arrows).
    # Returns: "press:<index>", "present:<index>", or loops.

    def _interaction_loop():
        """Blocking interaction loop for cross-examination."""
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

                # Open evidence panel
                store._aa_evidence_panel_open = True
                store._aa_selected_evidence = None
                renpy.show_screen("aa_evidence_panel")

                selected = renpy.call_screen("aa_evidence_select")
                store._aa_evidence_panel_open = False
                renpy.hide_screen("aa_evidence_panel")

                if selected is None:
                    continue  # cancelled

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

    # ─── penalty Statement ───────────────────────────────────────
    #
    # Syntax:  penalty <amount>

    def parse_penalty(lexer):
        amount = parse_integer(lexer)
        return {"amount": amount if amount is not None else 1}

    def execute_penalty(parsed):
        _aa.on_penalty(parsed["amount"])
        renpy.restart_interaction()

    register("penalty", parse=parse_penalty, execute=execute_penalty)

    # ─── get_evidence Statement ──────────────────────────────────
    #
    # Syntax:  get_evidence <evidence_id>

    def parse_get_evidence(lexer):
        ev_id = parse_name(lexer)
        if ev_id is None:
            ev_id = require(lexer, parse_string, "evidence id")
        return {"evidence_id": ev_id}

    def execute_get_evidence(parsed):
        ev_id = parsed["evidence_id"]
        ev_data = _aa._evidence_defs.get(ev_id)
        if ev_data is not None:
            store.court_record.add_evidence(ev_id, ev_data)
        else:
            raise Exception("Evidence '{}' not defined.".format(ev_id))
        renpy.restart_interaction()

    register("get_evidence", parse=parse_get_evidence, execute=execute_get_evidence)

    # ─── remove_evidence Statement ───────────────────────────────
    #
    # Syntax:  remove_evidence <evidence_id>

    def parse_remove_evidence(lexer):
        ev_id = parse_name(lexer)
        if ev_id is None:
            ev_id = require(lexer, parse_string, "evidence id")
        return {"evidence_id": ev_id}

    def execute_remove_evidence(parsed):
        store.court_record.remove_evidence(parsed["evidence_id"])
        renpy.restart_interaction()

    register("remove_evidence", parse=parse_remove_evidence, execute=execute_remove_evidence)

    # ─── set_flag Statement ──────────────────────────────────────
    #
    # Syntax:  set_flag <key> [to <value>]

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

    def execute_set_flag(parsed):
        store.court_record.set_flag(parsed["key"], parsed["value"])
        renpy.restart_interaction()

    register("set_flag", parse=parse_set_flag, execute=execute_set_flag)

    # ─── add_stmt Statement ──────────────────────────────────────
    #
    # Syntax:  add_stmt "text"
    # Used inside press blocks. Appends a new statement to testimony.

    def parse_add_stmt(lexer):
        text = require(lexer, parse_string, "statement text")
        return {"text": text}

    def execute_add_stmt(parsed):
        if store._aa_testimony_stmts is not None:
            store._aa_testimony_stmts.append(parsed["text"])
        renpy.restart_interaction()

    register("add_stmt", parse=parse_add_stmt, execute=execute_add_stmt)

    # ─── stmt Statement ──────────────────────────────────────────
    #
    # Syntax:  stmt "text"
    # Adds a statement to the current testimony list.

    def parse_stmt(lexer):
        text = require(lexer, parse_string, "statement text")
        return {"text": text}

    def execute_stmt(parsed):
        if store._aa_testimony_stmts is not None:
            store._aa_testimony_stmts.append(parsed["text"])
            store._aa_testimony_index = len(store._aa_testimony_stmts) - 1
        renpy.restart_interaction()

    register("stmt", parse=parse_stmt, execute=execute_stmt)

    # ─── end_testimony Statement ─────────────────────────────────
    #
    # Syntax:  end_testimony

    def parse_end_testimony(lexer):
        return {}

    def execute_end_testimony(parsed):
        store._aa_testimony_stmts = None
        store._aa_testimony_index = 0
        store._aa_testimony_title = ""
        store._aa_testimony_active = False
        _aa.on_testimony_complete()
        renpy.restart_interaction()

    register("end_testimony", parse=parse_end_testimony, execute=execute_end_testimony)

    # ─── begin_testimony Statement ───────────────────────────────
    #
    # Syntax:  begin_testimony "title" [by <character_id>]
    #
    # Opens testimony. Block contains stmt + press + present.
    # Execution:
    #   1. Execute all child nodes (stmts accumulate, press/present register handlers)
    #   2. Enter blocking interaction loop
    #   3. Route to correct handler based on player action
    #   4. Repeat until correct present or game over

    def parse_begin_testimony(lexer):
        title = require(lexer, parse_string, "testimony title")
        by_char = None
        if lexer.keyword("by"):
            by_char = require(lexer, parse_name, "character id")
        return {"title": title, "by": by_char}

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

        # Phase 1: Execute all child nodes linearly.
        # This accumulates stmts and registers press/present handlers.
        for node in block:
            renpy.execute(node)
            # If this is a press or present node, store its block as a handler
            if hasattr(node, 'parsed') and isinstance(node.parsed, dict):
                target = node.parsed.get("target")
                if target is not None and target == "current":
                    pass  # will be resolved at runtime

        # Phase 2: Enter blocking interaction loop
        while True:
            result = _interaction_loop()

            if result == "game_over":
                _aa.on_game_over()
                return None

            if result.startswith("present:"):
                # Correct present — find and execute the present handler block
                idx = int(result.split(":")[1])
                # Look for a present node in the block
                for node in block:
                    if _is_statement(node, "present"):
                        node_parsed = _get_node_parsed(node)
                        if node_parsed and _target_matches(node_parsed.get("target"), idx):
                            # Execute the present block
                            if hasattr(node, 'block') and node.block:
                                for child in node.block:
                                    renpy.execute(child)
                            break
                # Exit testimony
                store._aa_testimony_active = False
                renpy.restart_interaction()
                return None  # continue after begin_testimony block

            elif result.startswith("press:"):
                idx = int(result.split(":")[1])
                # Find and execute the press handler block
                for node in block:
                    if _is_statement(node, "press"):
                        node_parsed = _get_node_parsed(node)
                        if node_parsed and _target_matches(node_parsed.get("target"), idx):
                            if hasattr(node, 'block') and node.block:
                                for child in node.block:
                                    renpy.execute(child)
                            break
                # Loop back to interaction
                continue

        return None

    def _is_statement(node, name):
        """Check if a node is a registered AA statement with the given name."""
        # Ren'Py wraps registered statements in UserStatement objects
        node_name = getattr(node, 'name', None)
        if node_name:
            # node.name is like "renpy/00aa_statements.rpy:press"
            return name in node_name
        # Fallback: check the line/py_code
        line = getattr(node, 'line', None) or getattr(node, 'py_code', '')
        if line:
            return line.strip().startswith(name)
        return False

    def _get_node_parsed(node):
        """Extract the parsed data from a UserStatement node."""
        # Ren'Py stores the parsed data in node.parsed or node.arguments
        parsed = getattr(node, 'parsed', None)
        if parsed is not None:
            return parsed
        # Try to reconstruct from node properties
        return None

    def _target_matches(target, idx):
        """Check if a press/present target matches the given index."""
        if target == "current":
            return True
        if isinstance(target, int):
            return target == idx
        return False

    register(
        "begin_testimony",
        parse=parse_begin_testimony,
        execute=execute_begin_testimony,
        next=next_begin_testimony,
        block="script",
    )

    # ─── cross_examination Statement ─────────────────────────────
    #
    # Syntax:  cross_examination "title"
    #
    # Coarse-grained wrapper. Same as begin_testimony but with
    # different naming for clarity.

    def parse_cross_examination(lexer):
        title = require(lexer, parse_string, "cross-examination title")
        return {"title": title}

    def execute_cross_examination(parsed):
        execute_begin_testimony(parsed)

    def next_cross_examination(parsed, block):
        return next_begin_testimony(parsed, block)

    register(
        "cross_examination",
        parse=parse_cross_examination,
        execute=execute_cross_examination,
        next=next_cross_examination,
        block="script",
    )

    # ─── press Statement ─────────────────────────────────────────
    #
    # Syntax:  press <target>
    #          <block of Ren'Py script>
    #
    # When inside begin_testimony: registers as a handler.
    # When standalone: executes block immediately.

    def parse_press(lexer):
        target = parse_integer(lexer)
        if target is None:
            kw = parse_name(lexer)
            if kw == "current":
                target = "current"
            else:
                raise Exception("press requires an integer index or 'current'.")
        return {"target": target}

    def execute_press(parsed):
        store._aa_press_target = parsed["target"]
        renpy.restart_interaction()

    def next_press(parsed, block):
        # If inside a begin_testimony block, don't enter here —
        # begin_testimony handles routing.
        # If standalone, enter the block.
        if not store._aa_testimony_active:
            return block
        # Inside testimony: skip (begin_testimony will call the block when needed)
        return None

    register(
        "press",
        parse=parse_press,
        execute=execute_press,
        next=next_press,
        block="script",
    )

    # ─── present Statement ───────────────────────────────────────
    #
    # Syntax:  present <target> using <evidence_id> [or <evidence_id2>...]
    #          <block of Ren'Py script>
    #
    # When inside begin_testimony: registers as a handler.
    # When standalone: opens evidence panel and blocks until correct.

    def parse_present(lexer):
        target = parse_integer(lexer)
        if target is None:
            kw = parse_name(lexer)
            if kw == "current":
                target = "current"
            else:
                raise Exception("present requires an integer index or 'current'.")

        require(lexer, lambda l: l.keyword("using"), "'using' keyword")

        correct_ids = [require(lexer, parse_name, "evidence id")]
        while lexer.keyword("or"):
            correct_ids.append(require(lexer, parse_name, "evidence id"))

        return {"target": target, "correct_ids": correct_ids}

    def execute_present(parsed):
        store._aa_present_target = parsed["target"]
        store._aa_present_correct_ids = parsed["correct_ids"]
        renpy.restart_interaction()

    def next_present(parsed, block):
        # If inside begin_testimony, skip (handled by begin_testimony).
        if store._aa_testimony_active:
            return None

        # Standalone mode: block until correct present
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

    register(
        "present",
        parse=parse_present,
        execute=execute_present,
        next=next_present,
        block="script",
    )

    # ─── investigate Statement ───────────────────────────────────
    #
    # Syntax:  investigate "scene_name" at <location_id>
    #              hotspot "name" at (x, y) size (w, h) radius r:
    #                  examine hotspot_id:
    #                      "dialogue"
    #                      get_evidence some_id
    #
    # Block contains hotspot definitions. Each hotspot's block
    # contains examine handlers. The interaction loop shows the
    # scene, waits for hotspot clicks, and executes examine blocks.

    def parse_investigate(lexer):
        scene_name = require(lexer, parse_string, "scene name")
        loc_id = None
        if lexer.keyword("at"):
            loc_id = require(lexer, parse_name, "location id")
        return {"scene_name": scene_name, "location_id": loc_id}

    def execute_investigate(parsed):
        store._aa_investigation_active = True
        store._aa_investigation_location = parsed["location_id"]
        store._aa_examine_handlers = {}
        renpy.restart_interaction()

    def next_investigate(parsed, block):
        if block is None:
            return None

        # Phase 1: Collect hotspot definitions and their examine handlers.
        _aa._hotspot_defs = {}
        for node in block:
            if _is_statement(node, "hotspot"):
                node_parsed = _get_node_parsed(node)
                if node_parsed:
                    hid = node_parsed.get("hotspot_id")
                    if hid:
                        _aa._hotspot_defs[hid] = node_parsed
                        # Collect examine child nodes from this hotspot's block
                        if hasattr(node, 'block') and node.block:
                            for child in node.block:
                                if _is_statement(child, "examine"):
                                    ex_parsed = _get_node_parsed(child)
                                    if ex_parsed:
                                        ex_hid = ex_parsed.get("hotspot_id")
                                        if ex_hid:
                                            store._aa_examine_handlers[ex_hid] = child

        # Phase 2: Blocking interaction loop.
        # Show scene, wait for hotspot click, execute examine handler, repeat.
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

            # Mark hotspot as examined
            store.court_record.mark_examined(hotspot_id)
            _aa.on_hotspot_examined(hotspot_id)

            # Find and execute the examine handler for this hotspot
            examine_node = store._aa_examine_handlers.get(hotspot_id)
            if examine_node is not None and hasattr(examine_node, 'block') and examine_node.block:
                for child in examine_node.block:
                    renpy.execute(child)

            renpy.restart_interaction()

        # Clean up
        store._aa_investigation_active = False
        store._aa_investigation_location = None
        _aa._hotspot_defs = {}
        store._aa_examine_handlers = {}
        renpy.restart_interaction()
        return None

    register(
        "investigate",
        parse=parse_investigate,
        execute=execute_investigate,
        next=next_investigate,
        block="script",
    )

    # ─── hotspot Statement ───────────────────────────────────────
    #
    # Syntax:  hotspot "name" at (x, y) size (w, h) [radius r]
    #              examine hotspot_id:
    #                  "dialogue"
    #
    # Block contains examine handlers. Skipped during linear execution;
    # blocks are collected by the parent investigate statement.

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

    def execute_hotspot(parsed):
        # No-op: hotspot definitions are collected by investigate's next function.
        pass

    def next_hotspot(parsed, block):
        # Don't enter block during linear execution.
        return None

    register(
        "hotspot",
        parse=parse_hotspot,
        execute=execute_hotspot,
        next=next_hotspot,
        block="script",
    )

    # ─── examine Statement ───────────────────────────────────────
    #
    # Syntax:  examine <hotspot_id>:
    #              "dialogue text"
    #              get_evidence some_id
    #
    # Block is executed when the corresponding hotspot is clicked.
    # Skipped during linear execution; collected by investigate.

    def parse_examine(lexer):
        hotspot_id = require(lexer, parse_name, "hotspot id")
        return {"hotspot_id": hotspot_id}

    def execute_examine(parsed):
        # No-op: examine handlers are executed by investigate's interaction loop.
        pass

    def next_examine(parsed, block):
        # Don't enter block during linear execution.
        return None

    register(
        "examine",
        parse=parse_examine,
        execute=execute_examine,
        next=next_examine,
        block="script",
    )

    # ─── end_investigate Statement ───────────────────────────────

    def parse_end_investigate(lexer):
        return {}

    def execute_end_investigate(parsed):
        store._aa_investigation_active = False
        store._aa_investigation_location = None
        renpy.restart_interaction()

    register("end_investigate", parse=parse_end_investigate, execute=execute_end_investigate)

    # ─── talk Statement ──────────────────────────────────────────
    #
    # Syntax:  talk <npc_id>:
    #              topic "name":
    #                  "dialogue"
    #              present evidence_id:
    #                  "NPC reaction"
    #
    # Block contains topic and present handlers. Shows a menu,
    # executes selected handler, loops until player exits.

    def parse_talk(lexer):
        npc_id = require(lexer, parse_name, "NPC id")
        return {"npc_id": npc_id}

    def execute_talk(parsed):
        store._aa_talk_npc = parsed["npc_id"]
        store._aa_talk_topic_handlers = {}
        store._aa_talk_present_handlers = {}
        renpy.restart_interaction()

    def next_talk(parsed, block):
        if block is None:
            return None

        npc_id = parsed["npc_id"]

        # Phase 1: Collect topic and present handlers.
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

        # Phase 2: Interaction loop — show menu, handle choices.
        while True:
            # Build available topics (not yet talked about)
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
                # Open evidence selection
                selected = renpy.call_screen("aa_evidence_select")
                if selected is not None:
                    # Check if NPC has a handler for this evidence
                    present_node = store._aa_talk_present_handlers.get(selected)
                    if present_node is not None:
                        store.court_record.mark_evidence_presented(npc_id, selected)
                        if hasattr(present_node, 'block') and present_node.block:
                            for child in present_node.block:
                                renpy.execute(child)
                    else:
                        # Default reaction
                        renpy.say(None, "这个不太相关吧……")
                    renpy.restart_interaction()

            elif choice in store._aa_talk_topic_handlers:
                # Mark topic as talked and execute its block
                store.court_record.mark_topic_talked(npc_id, choice)
                topic_node = store._aa_talk_topic_handlers[choice]
                if hasattr(topic_node, 'block') and topic_node.block:
                    for child in topic_node.block:
                        renpy.execute(child)
                renpy.restart_interaction()

        # Clean up
        store._aa_talk_npc = None
        store._aa_talk_topic_handlers = {}
        store._aa_talk_present_handlers = {}
        renpy.restart_interaction()
        return None

    register(
        "talk",
        parse=parse_talk,
        execute=execute_talk,
        next=next_talk,
        block="script",
    )

    # ─── topic Statement ─────────────────────────────────────────
    #
    # Syntax:  topic "name":
    #              "dialogue line 1"
    #              "dialogue line 2"
    #
    # Block is executed when the topic is selected from talk menu.
    # Skipped during linear execution; collected by parent talk.

    def parse_topic(lexer):
        topic_name = require(lexer, parse_string, "topic name")
        return {"topic_name": topic_name}

    def execute_topic(parsed):
        pass  # No-op: collected by talk's next function

    def next_topic(parsed, block):
        return None  # Don't enter block during linear execution

    register(
        "topic",
        parse=parse_topic,
        execute=execute_topic,
        next=next_topic,
        block="script",
    )

    # ─── move Statement ──────────────────────────────────────────
    #
    # Syntax:  move <location_id>
    #          move <location_id> if <condition>
    #
    # Switches to another investigation location.

    def parse_move(lexer):
        loc_id = require(lexer, parse_name, "location id")
        condition = None
        if lexer.keyword("if"):
            condition = require(lexer, parse_name, "condition flag")
        return {"location_id": loc_id, "condition": condition}

    def execute_move(parsed):
        loc_id = parsed["location_id"]
        condition = parsed.get("condition")

        # Check condition
        if condition and not store.court_record.has_flag(condition):
            renpy.say(None, "现在没有必要去那里。")
            renpy.restart_interaction()
            return

        # Check location exists
        loc = store.court_record.get_location(loc_id)
        if loc is None:
            raise Exception("Location '{}' not defined.".format(loc_id))

        # Switch location
        store._aa_investigation_location = loc_id

        # Play BGM if defined
        if loc.bgm:
            try:
                renpy.music.play(loc.bgm, channel="music")
            except Exception:
                pass

        renpy.restart_interaction()

    register("move", parse=parse_move, execute=execute_move)


# ─── Blocking Screens ────────────────────────────────────────────
# These screens block (using `call screen`) until the player acts.

screen aa_testimony_interact():
    # This screen is shown via `call screen`. It waits indefinitely
    # for the player to press Z, X, or arrow keys.
    # Returns a string action like "press:0", "present:2", etc.

    modal False
    zorder 80

    $ stmts = _aa_testimony_stmts or []
    $ idx = _aa_testimony_index

    # Z — press current statement
    if len(stmts) > 0:
        key "K_z" action Return("press:{}".format(idx))

    # X — present on current statement
    if len(stmts) > 0:
        key "K_x" action Return("present:{}".format(idx))

    # Arrow keys — navigate
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

    # Space/Enter — just advance (no action, refresh)
    key "K_SPACE" action NullAction()
    key "K_RETURN" action NullAction()

screen aa_evidence_select():
    # This screen is shown via `call screen` during evidence selection.
    # It waits for the player to select an evidence item or press ESC.
    # Returns the selected evidence ID, or None if cancelled.

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


# ─── Investigation Scene Screen ──────────────────────────────────
# Shown via `call screen` during investigation. Renders the scene
# using SceneDisplayable and returns the clicked hotspot ID.

screen aa_investigation_scene(location_id, hotspot_defs):
    # This screen is shown via `call screen`. It renders the
    # investigation scene and returns the hotspot ID when the player
    # interacts, or "__exit__" to leave.

    modal False
    zorder 80

    $ scene = _aa.SceneDisplayable(location_id, hotspot_defs)
    add scene

    # Periodic timer to keep animation and input smooth
    timer 0.016 action Function(renpy.restart_interaction) repeat True

    # Navigation hint
    frame:
        xalign 0.5
        ypos 10
        background "#000000aa"
        xpadding 15
        ypadding 5
        text "WASD/方向键移动 | E/点击交互 | ESC退出":
            size 14
            color "#888888"

    # ESC to exit investigation
    key "K_ESCAPE" action Return("__exit__")


# ─── Talk Menu Screen ────────────────────────────────────────────
# Shown via `call screen` during NPC dialogue. Returns the selected
# topic name, "__present__" for evidence presentation, or "__exit__".

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

            # Topic buttons
            if len(topics) > 0:
                for tname in topics:
                    textbutton tname:
                        xalign 0.5
                        text_size 22
                        action Return(tname)
            else:
                text "（没有更多话题）" size 18 color "#888888" xalign 0.5

            null height 10

            # Present evidence button
            if has_present:
                textbutton "出示证物":
                    xalign 0.5
                    text_size 22
                    text_color "#44cc44"
                    action Return("__present__")

            # End conversation
            textbutton "结束对话":
                xalign 0.5
                text_size 18
                text_color "#888888"
                action Return("__exit__")

    key "K_ESCAPE" action Return("__exit__")


# ─── Helper ──────────────────────────────────────────────────────

init -997 python in _aa_stmt:
    def _play_ding():
        """Play the testimony 'ding' sound when switching statements."""
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
