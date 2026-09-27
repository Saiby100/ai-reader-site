from __future__ import annotations

PUA_FR = ""  # stands in for the 'fr' ligature glyph
PUA_FT = ""  # stands in for the 'ft' ligature glyph


def _el(**kwargs: object):
    from app.models import DocumentElement

    kwargs.setdefault("type", "paragraph")
    return DocumentElement(**kwargs)


def test_collect_pua_counts_across_tree_and_fields() -> None:
    from app.parsing.ligatures import _collect_pua

    tree = [
        _el(text=f"O{PUA_FT}en and A{PUA_FR}ica"),
        _el(
            type="table",
            html=f"<td>{PUA_FR}om</td>",
            children=[_el(text=f"le{PUA_FT}")],
        ),
        _el(text="clean paragraph, no broken glyphs"),
    ]
    counts = _collect_pua(tree)
    assert counts[PUA_FT] == 2  # 'Often' + 'left'
    assert counts[PUA_FR] == 2  # 'Africa' + 'from' (in table html)
    assert sum(counts.values()) == 4


def test_apply_glyph_map_strips_pads_keeps_boundaries_and_clears_charspan() -> None:
    from app.parsing.ligatures import _apply_glyph_map

    mapping = {PUA_FT: "ft", PUA_FR: "fr"}
    # Raw-layer truth (prefix, suffix) per glyph; empty side == real word boundary there.
    # 'often'/'left' are mid-word (pad spaces); 'from' is word-initial (the leading space is
    # a real boundary, identical in Docling's text to the mid-word pad case).
    glyph_words = {
        PUA_FT: [("o", "en"), ("le", "")],  # 'often', 'left'
        PUA_FR: [("", "om")],  # 'from'
    }
    mid = _el(text=f"O {PUA_FT} en", charspan=(0, 5))  # 'Often' -> strip both pads
    initial = _el(text=f"goods {PUA_FR} om here", charspan=(0, 9))  # 'goods from here'
    final = _el(text=f"le {PUA_FT} .", charspan=(0, 4))  # 'left.' -> word-final, keep boundary
    clean = _el(text="untouched", charspan=(0, 9))

    _apply_glyph_map([mid, initial, final, clean], mapping, glyph_words)

    assert mid.text == "Often"
    assert initial.text == "goods from here"
    assert final.text == "left ."
    # rewritten elements drop their now-stale charspan; the clean one keeps it
    assert mid.charspan is None and initial.charspan is None and final.charspan is None
    assert clean.text == "untouched" and clean.charspan == (0, 9)


def test_apply_glyph_map_without_boundary_data_never_fuses_words() -> None:
    from app.parsing.ligatures import _apply_glyph_map

    # With no raw-layer data, a flanking space is kept rather than risk joining two words.
    # This is the word-initial shape Docling actually emits (leading boundary, no trailing pad).
    initial = _el(text=f"extraordinary {PUA_FR}eedom")
    _apply_glyph_map([initial], {PUA_FR: "fr"}, {})
    assert initial.text == "extraordinary freedom"


def test_apply_glyph_map_recurses_into_children() -> None:
    from app.parsing.ligatures import _apply_glyph_map

    glyph_words = {PUA_FR: [("a", "ica")], PUA_FT: [("o", "en")]}  # 'Africa', 'Often'
    parent = _el(text=f"A{PUA_FR}ica", children=[_el(text=f"O{PUA_FT}en")])
    _apply_glyph_map([parent], {PUA_FR: "fr", PUA_FT: "ft"}, glyph_words)
    assert parent.text == "Africa"
    assert parent.children[0].text == "Often"


def test_contiguous_ranges_collapses_runs() -> None:
    from app.parsing.ligatures import _contiguous_ranges

    assert _contiguous_ranges([5, 6, 7, 40]) == [(5, 7), (40, 40)]
    assert _contiguous_ranges([40, 5, 6]) == [(5, 6), (40, 40)]
    assert _contiguous_ranges([]) == []
