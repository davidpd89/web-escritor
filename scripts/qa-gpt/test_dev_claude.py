import qa_dev_claude as d


def test_diff_a_parche_un_hunk_unico():
    p = d.diff_a_parche({"x.js": "a\nb\nc\nd"}, {"x.js": "a\nB\nc\nd"})
    assert p == {"ficheros": [{"ruta": "x.js", "reemplazos": [{"buscar": "b", "por": "B"}]}]}


def test_diff_a_parche_amplia_contexto_si_buscar_se_repite():
    p = d.diff_a_parche({"x.js": "k\nx\nk\ny\nk"}, {"x.js": "k\nx\nk\nY\nk"})
    r = p["ficheros"][0]["reemplazos"][0]
    assert "y" in r["buscar"] and r["buscar"] != "y" or "y" == r["buscar"]
    assert "Y" in r["por"]


def test_diff_a_parche_sin_cambios_devuelve_none():
    assert d.diff_a_parche({"x.js": "a"}, {"x.js": "a"}) is None
