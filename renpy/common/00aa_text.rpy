# Ace Attorney Ren'Py — Text Presentation Layer
# Typewriter beep sounds, character-specific audio, custom TextTags.

init -997 python in _aa_text:

    import renpy
    import store

    _aa = renpy.store._aa

    # ─── Audio Channel Setup ─────────────────────────────────────

    # Register a dedicated channel for beep sounds so they don't
    # conflict with BGM or SFX channels.
    renpy.music.register_channel("aa_beep", mixer="sfx", loop=False)

    # Track whether text is currently being displayed (for beep control)
    _text_active = False
    _current_beep_path = None

    # ─── Character Callback ──────────────────────────────────────
    #
    # Called by Ren'Py on character events:
    #   "begin"  — before text is shown
    #   "show"   — text segment is about to be displayed
    #   "show_done" — text has been fully displayed (or skipped)
    #   "end"    — after interaction completes
    #   "slow_done" — typewriter effect finished

    def _aa_char_callback(event, **kwargs):
        global _text_active, _current_beep_path

        if event == "begin":
            _text_active = True
            # Get the beep path from the current character context
            beep = _current_beep_path or _aa.beep_presets.get(_aa.default_beep, "")
            if beep:
                try:
                    renpy.audio.music.play(beep, channel="aa_beep", loop=True)
                except Exception:
                    pass

        elif event == "slow_done" or event == "end":
            if _text_active:
                _text_active = False
                try:
                    renpy.audio.music.stop(channel="aa_beep")
                except Exception:
                    pass

        elif event == "show":
            # For per-segment sound, we could change the beep here.
            # Currently the beep loops from "begin" until "slow_done"/"end".
            pass

    # ─── Default beep callback (no character context) ────────────

    def _aa_default_callback(event, **kwargs):
        global _current_beep_path, _text_active
        _current_beep_path = None
        _aa_char_callback(event, **kwargs)

    # ─── Per-Character beep callback factory ─────────────────────

    def make_beep_callback(profile_id):
        """
        Returns a callback function for a specific character's beep sound.
        """
        def callback(event, **kwargs):
            global _current_beep_path, _text_active

            if event == "begin":
                profile = store.court_record.get_profile(profile_id)
                if profile:
                    _current_beep_path = profile.get_beep_path()
                else:
                    _current_beep_path = None

            _aa_char_callback(event, **kwargs)

        return callback

    # ─── Character Factory ───────────────────────────────────────

    def make_aa_character(profile_id, **kwargs):
        """
        Creates a Ren'Py Character with the AA beep callback.

        Usage:
            define phoenix = _aa_text.make_aa_character("phoenix", color="#c8ffc8")
            phoenix "Hello, world!"
        """
        callback = make_beep_callback(profile_id)

        # Get the character name from the profile
        profile = store.court_record.get_profile(profile_id)
        name = profile.name if profile else profile_id
        color = kwargs.pop("color", profile.color if profile else "#ffffff")

        return renpy.store.Character(
            name,
            color=color,
            callback=callback,
            **kwargs
        )

    # ─── Narrator Character (with default beep) ──────────────────

    def _make_narrator():
        return renpy.store.Character(
            None,
            callback=_aa_default_callback,
        )


# ─── Store-level convenience ─────────────────────────────────────

# Narrator with beep
default narrator = _aa_text._make_narrator()

# Alias for Character factory
init -996 python:
    aa_make_character = _aa_text.make_aa_character


# ─── Custom TextTags ─────────────────────────────────────────────
#
# Usage in .rpy scripts:
#   "This is normal text {aa_pause=1.0}and this pauses for 1 second."
#   "This is {aa_speed=30}slow text{/aa_speed} and this is normal."
#
# NOTE: Custom TextTags require engine-level support.
# For now, we use Ren'Py's existing tags as workarounds:
#   {w}   — wait for click (standard Ren'Py)
#   {p}   — pause and wait for click
#   {fast} — show remaining text instantly
#
# Full custom TextTag support will be added in a future step
# if the standard tags prove insufficient.

init -996 python:
    # Store the text tag definitions for documentation purposes.
    # Actual implementation requires modifying renpy.text.text.Text.
    _aa_text_tags = {
        "aa_pause": "Pause for N seconds (auto-advance, no click required)",
        "aa_speed": "Change text speed to N cps within this tag range",
        "aa_shake": "Shake the text within this tag range",
        "aa_big": "Enlarge text within this tag range (for emphasis shouts)",
    }
