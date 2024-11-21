from lyricsheets.effect.template_effect import Template
from lyricsheets.models.karaoke import KObject
from unittest.mock import Mock
import pytest


@pytest.fixture
def mock_kobject():
    # Create a mock object for KObject
    mock_kobj = Mock(spec=KObject)

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
    # mock_kobj.text = "Some text"
    # mock_kobj.start = timedelta(seconds=10)
    # mock_kobj.end = timedelta(seconds=20)
    # mock_kobj.width = 100.0
    # mock_kobj.height = 50.0
    # mock_kobj.left = 0.0
    # mock_kobj.center = 50.0
    # mock_kobj.right = 100.0
    # mock_kobj.top = 0.0
    # mock_kobj.middle = 25.0
    # mock_kobj.bottom = 50.0
    # mock_kobj.x = 10.0
    # mock_kobj.y = 20.0

    return mock_kobj


@pytest.mark.parametrize(
    "inline, result",
    [
        ("$x $y", "100 200"),
        ("$dur, $x, $x", "400, 100, 100"),
        ("$y $left $dur", "200 300 400"),
        ("$lmao", "19920808"),
    ],
)
def test_template_inline_text(mock_kobject, inline: str, result: str):
    text = Template._split_inline(inline)
    inlined = text.get_text(mock_kobject)
    assert inlined == result
