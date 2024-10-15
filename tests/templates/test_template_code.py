from lyricsheets.effect.template_effect import TemplateEffect

import pytest


@pytest.mark.parametrize(
    "text, data",
    [
        ('retime("presyl", 100, 200)', ("retime", ["presyl", 100, 200])),
        ('retime("prechar", 13, 250)', ("retime", ["prechar", 13, 250])),
        ("do_nothing()", ("do_nothing", [])),
    ],
)
def test_template_function_parse(text: str, data):
    fndata = TemplateEffect._get_function_data(text)
    assert fndata == data
