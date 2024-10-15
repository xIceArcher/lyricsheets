from lyricsheets.effect.template_effect import Template, TemplateType
import pytest


@pytest.mark.parametrize(
    "template, type",
    [
        ("template line: 11", TemplateType.LINE),
        ("template pre-line: 11", TemplateType.PRELINE),
        ("template char: 11", TemplateType.CHAR),
        ("template syl: 11", TemplateType.SYL),
        ("template syl char: 11", TemplateType.CHAR),
        ("template syl: char", TemplateType.SYL),
        ("template: 11", TemplateType.SYL),
    ],
)
def test_template_type(template: str, type):
    tmp = Template.compile(template)
    assert tmp.templateType == type


@pytest.mark.parametrize(
    "template, noblank",
    [
        ("template syl: 11", False),
        ("template noblank: 11", True),
        ("template syl noblank: 11", True),
        ("template char syl noblank: 11", True),
        ("template syl: noblank", False),
    ],
)
def test_template_noblank(template: str, noblank: bool):
    tmp = Template.compile(template)
    assert tmp.noblank == noblank


@pytest.mark.parametrize(
    "template, notext",
    [
        ("template syl: 11", False),
        ("template notext: 11", True),
        ("template syl notext: 11", True),
        ("template char syl notext: 11", True),
        ("template syl: notext", False),
    ],
)
def test_template_notext(template: str, notext: bool):
    tmp = Template.compile(template)
    assert tmp.notext == notext


@pytest.mark.parametrize(
    "template, repeat",
    [
        ("template syl: 11", 1),
        ("template line repeat 11: 11", 11),
        ("template line loop 11: 11", 11),
        ("template char repeat 120: 100", 120),
        ("template char loop 30 repeat 59: 11", 30),
    ],
)
def test_template_repeat(template: str, repeat: int):
    tmp = Template.compile(template)
    assert tmp.repeat == repeat


@pytest.mark.parametrize(
    "template, parts",
    [
        (r"template syl: {}", [r"{}"]),
        (r"template syl: {$x}", [r"{", "$x", "}"]),
        (r"template syl: $x + $y", ["$x", " + ", "$y"]),
        (r"template syl: $Y", ["$y"]),
        (r"template syl: $x$y$height", ["$x", "$y", "$height"]),
    ],
)
def test_template_inline(template: str, parts: list[str]):
    tmp = Template.compile(template)
    assert len(tmp.parts) == 1
    assert tmp.parts[0].parts == parts


@pytest.mark.parametrize(
    "template, parts",
    [
        ("template syl: !x!", [["!x!"]]),
        ("template syl: !x!,y", [["!x!"], [",y"]]),
        ("template syl: (!1+1!, !2+2!)", [["("], ["!1+1!"], [", "], ["!2+2!"], [")"]]),
        ("template syl: !1+$x+$y+$z!", [["!1+", "$x", "+", "$y", "+", "$z", "!"]]),
        (
            "template syl: !$x+$y!,!$top+$bottom!",
            [["!", "$x", "+", "$y", "!"], [","], ["!", "$top", "+", "$bottom", "!"]],
        ),
    ],
)
def test_template_code(template: str, parts: list[list[str]]):
    tmp = Template.compile(template)
    tparts = [tpart.parts for tpart in tmp.parts]
    assert tparts == parts
