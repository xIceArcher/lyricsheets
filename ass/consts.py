from datetime import timedelta

import pyass

# Styles
DIVIDER_STYLE = pyass.Style(
    name="Song - Divider",
)

TITLE_STYLE = pyass.Style(
    name="Song - Title",
    fontName="Museo Sans 900",
    fontSize=30,
    primaryColor=pyass.Color(r=0xFF, g=0xFF, b=0xFF, a=0x0A),
    secondaryColor=pyass.Color(a=0xF0),
    outlineColor=pyass.Color(a=0x0A),
    backColor=pyass.Color(r=0xD6, g=0x1E, b=0xA8),
    outline=3.0,
    shadow=0.0,
    alignment=pyass.Alignment.BOTTOM_LEFT,
    marginL=29,
    marginR=29,
    marginV=29,
)

ROMAJI_STYLE = pyass.Style(
    name="Song - JP",
    fontName="Proxima Nova Th",
    fontSize=58,
    isBold=True,
    outline=1.5,
    shadow=1.0,
    marginL=246,
    marginR=246,
    marginV=45,
)

EN_STYLE = pyass.Style(
    name="Song - EN",
    fontName="Avenir Next Rounded Pro",
    fontSize=40,
    isBold=True,
    outline=1.5,
    shadow=1.0,
    marginL=113,
    marginR=113,
    marginV=45,
)

# Tags
TITLE_CARD_TAGS = pyass.Tags(
    [
        pyass.FadeTag(200, 200),
        pyass.BlurEdgesTag(11),
        pyass.AlignmentTag(pyass.Alignment.TOP_LEFT),
    ]
)

LYRICS_TAGS = pyass.Tags(
    [
        pyass.FadeTag(200, 200),
        pyass.BlurEdgesTag(11),
        pyass.AlignmentTag(pyass.Alignment.CENTER),
    ]
)

ROMAJI_POS_TAG = pyass.PositionTag(960, 960)
NO_EN_ROMAJI_POS_TAG = pyass.PositionTag(960, 1010)
SECONDARY_ROMAJI_POS_TAG = pyass.PositionTag(960, 65)

EN_POS_TAG = pyass.PositionTag(960, 1015)
SECONDARY_EN_POS_TAG = pyass.PositionTag(960, 120)

# Effects
KARAOKE_EFFECT = "karaoke"

# Timings
TITLE_EVENT_DURATION = timedelta(seconds=5)
DEFAULT_SWITCH_DURATION = timedelta(milliseconds=200)
DEFAULT_TRANSITION_DURATION = timedelta(milliseconds=500)
