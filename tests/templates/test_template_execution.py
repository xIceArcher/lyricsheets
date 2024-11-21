from enum import Enum
from lyricsheets.effect.template_effect import Template, TemplateEffect
from lyricsheets.models.karaoke import KLine, KChar, KSyl
from unittest.mock import Mock, PropertyMock, patch
from datetime import timedelta
import pyass
import pytest


class kObjectType(Enum):
    KCHAR = 0
    KSYL = 1
    KLINE = 2


def create_mock_template(layer: int):
    mockTemplate = Mock(spec=Template)

    mockTemplate.parts = []
    mockTemplate.layer = layer

    return mockTemplate


def create_mock_kObject(
    isAlone: bool,
    isEN: bool,
    lineStart: int,
    lineEnd: int,
    style: str,
    testType: kObjectType,
):
    kLine = Mock(spec=KLine)
    kLine.isAlone = isAlone
    kLine.isEN = isEN

    start = PropertyMock(return_value=timedelta(milliseconds=lineStart))
    end = PropertyMock(return_value=timedelta(milliseconds=lineEnd))

    type(kLine).start = start
    type(kLine).end = end

    if testType == kObjectType.KCHAR:
        kChar = Mock(spec=KChar)
        kChar.kLine = kLine
        kChar.style = Mock(spec=pyass.Style)
        kChar.style.name = style

        return kChar
    elif testType == kObjectType.KSYL:
        kSyl = Mock(spec=KSyl)
        kSyl.kLine = kLine
        kSyl.style = Mock(spec=pyass.Style)
        kSyl.style.name = style

        return kSyl
    else:
        kLine.style = Mock(spec=pyass.Style)
        kLine.style.name = style
        kLine.kLine = kLine

        return kLine


@pytest.mark.parametrize("layer", [0, 1, 2, 3, 4, 99])
def test_template_execution_layer(layer: int):
    template = create_mock_template(layer)
    kLine = create_mock_kObject(False, False, 0, 1000, "Test", kObjectType.KLINE)

    templateEffect = TemplateEffect()
    event = templateEffect.execute_template(template, kLine)

    assert event.layer == layer


@pytest.mark.parametrize(
    "isEN, isAlone, format, type",
    [
        (False, False, pyass.EventFormat.DIALOGUE, kObjectType.KCHAR),
        (False, True, pyass.EventFormat.DIALOGUE, kObjectType.KCHAR),
        (True, False, pyass.EventFormat.DIALOGUE, kObjectType.KCHAR),
        (True, True, pyass.EventFormat.COMMENT, kObjectType.KCHAR),
        (False, False, pyass.EventFormat.DIALOGUE, kObjectType.KSYL),
        (False, True, pyass.EventFormat.DIALOGUE, kObjectType.KSYL),
        (True, False, pyass.EventFormat.DIALOGUE, kObjectType.KSYL),
        (True, True, pyass.EventFormat.COMMENT, kObjectType.KSYL),
        (False, False, pyass.EventFormat.DIALOGUE, kObjectType.KLINE),
        (False, True, pyass.EventFormat.DIALOGUE, kObjectType.KLINE),
        (True, False, pyass.EventFormat.DIALOGUE, kObjectType.KLINE),
        (True, True, pyass.EventFormat.COMMENT, kObjectType.KLINE),
    ],
)
def test_template_execution_format(
    isEN: bool, isAlone: bool, format: pyass.EventFormat, type: kObjectType
):
    template = create_mock_template(0)
    kObject = create_mock_kObject(isEN, isAlone, 0, 1000, "Test", type)

    templateEffect = TemplateEffect()
    event = templateEffect.execute_template(template, kObject)

    assert event.format == format


@pytest.mark.parametrize(
    "style, type",
    [
        ("123", kObjectType.KCHAR),
        ("123", kObjectType.KLINE),
        ("123", kObjectType.KSYL),
        ("456", kObjectType.KCHAR),
        ("456", kObjectType.KLINE),
        ("456", kObjectType.KSYL),
    ],
)
def test_template_execution_style(style: str, type: kObjectType):
    template = create_mock_template(0)
    kObject = create_mock_kObject(False, False, 0, 1000, style, type)

    templateEffect = TemplateEffect()
    event = templateEffect.execute_template(template, kObject)

    assert event.style == style


@pytest.mark.parametrize(
    "start, end, type",
    [
        (125, 1250, kObjectType.KCHAR),
        (125, 1250, kObjectType.KSYL),
        (125, 1250, kObjectType.KLINE),
    ],
)
def test_template_execution_timing(start: int, end: int, type: kObjectType):
    template = create_mock_template(0)
    kObject = create_mock_kObject(False, False, start, end, "Test", type)

    templateEffect = TemplateEffect()
    event = templateEffect.execute_template(template, kObject)

    assert event.start == timedelta(milliseconds=start)
    assert event.end == timedelta(milliseconds=end)
