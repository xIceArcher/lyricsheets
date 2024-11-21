from lyricsheets.effect.template_effect import Template
from lyricsheets.models.karaoke import KChar, KSyl, KLine
from unittest.mock import Mock
from types import MethodType
import pytest


def create_mock_kobject():
    # Create a mock object for KObject
    mock_kobj = Mock(spec=KChar)

    def custom_inline_var(inline_name):
        match inline_name:
            case "x":
                return 100
            case "y":
                return 200
            case "left":
                return 300
            case "dur":
                return 400
            case _:
                return 19920808

    # Define the behavior of the abstract methods and properties
    mock_kobj.inline_var.side_effect = custom_inline_var  # Example value for inline_var
    return mock_kobj


def create_mock_kline():
    # Create a mock for KLine with a call tracker
    mockKLine = Mock(spec=KLine)
    mockKLine.call_count = 0

    # Mock implementation that increments the counter
    def mock_inline_var(self, inline_name):
        mockKLine.call_count += 1
        return None  # Mock does nothing and returns None

    # Assign the mock implementation to a method
    mockKLine.inline_var = MethodType(mock_inline_var, mockKLine)

    return mockKLine


def create_mock_ksyl():
    # Create a mock for KSyl
    mockKSyl = Mock(spec=KSyl)

    # Counter for method calls
    mockKSyl.call_count = 0

    # Mock implementation that increments the counter
    def mock_inline_var(self, inline_name):
        mockKSyl.call_count += 1
        return None  # Mock does nothing and returns None

    # Assign the mock implementation to the method
    mockKSyl.inline_var = MethodType(mock_inline_var, mockKSyl)

    return mockKSyl


def create_inline_test_kchar():
    mockKChar = Mock(spec=KChar)

    mockKChar.inline_var = MethodType(KChar.inline_var, mockKChar)
    mockKChar.kSyl = create_mock_ksyl()
    mockKChar.kLine = create_mock_kline()

    return mockKChar


def create_inline_test_ksyl():
    mockKSyl = Mock(spec=KSyl)

    mockKSyl.inline_var = MethodType(KSyl.inline_var, mockKSyl)
    mockKSyl.kLine = create_mock_kline()

    return mockKSyl


@pytest.mark.parametrize(
    "inline, result",
    [
        ("$x $y", "100 200"),
        ("$dur, $x, $x", "400, 100, 100"),
        ("$y $left $dur", "200 300 400"),
        ("$lmao", "19920808"),
    ],
)
def test_template_inline_text(inline: str, result: str):
    mock_kobject = create_mock_kobject()
    text = Template._split_inline(inline)
    inlined = text.get_text(mock_kobject)
    assert inlined == result


@pytest.mark.parametrize(
    "inlines, count",
    [(["test", "test2", "ltest", "l123"], 2), (["xx", "lxx", "yy", "lyy"], 2)],
)
def test_template_inline_syl_redirection(inlines: list[str], count: int):
    kSyl = create_inline_test_ksyl()
    for inline in inlines:
        kSyl.inline_var(inline)

    assert kSyl.kLine.call_count == count


@pytest.mark.parametrize(
    "inlines, countSyl, countLine",
    [(["test", "stest2", "ltest", "l123"], 1, 2), (["xx", "lxx", "yy", "syy"], 1, 1)],
)
def test_template_inline_char_redirection(inlines: list[str], countSyl: int, countLine):
    kChar = create_inline_test_kchar()
    for inline in inlines:
        kChar.inline_var(inline)

    assert kChar.kSyl.call_count == countSyl
    assert kChar.kLine.call_count == countLine
