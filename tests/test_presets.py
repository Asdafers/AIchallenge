from methodic.presets import PRESETS, get_preset

def test_presets_has_three_entries():
    assert len(PRESETS) == 3
    assert "lost_deals" in PRESETS
    assert "churn" in PRESETS
    assert "competitive" in PRESETS

def test_preset_has_required_keys():
    for preset in PRESETS.values():
        assert "title" in preset
        assert "brief" in preset
        assert "persona_hint" in preset
        assert len(preset["brief"]) > 20

def test_get_preset_returns_preset():
    p = get_preset("lost_deals")
    assert p["title"] == "Q1 2026 Lost Deal Analysis"

def test_get_preset_returns_none_for_unknown():
    assert get_preset("nonexistent") is None
