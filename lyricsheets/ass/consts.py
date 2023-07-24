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
    fontName="Proxima Nova",
    fontSize=58,
    primaryColor=pyass.Color(r=0xFF, g=0xFF, b=0xFF),
    secondaryColor=pyass.Color(a=0x00),
    outlineColor=pyass.Color(r=0xA5, g=0x46, b=0x9B),
    backColor=pyass.Color(r=0x72, g=0x30, b=0x6B),
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
    primaryColor=pyass.Color(r=0xFF, g=0xFF, b=0xFF),
    outlineColor=pyass.Color(r=0xA5, g=0x46, b=0x9B),
    backColor=pyass.Color(r=0x72, g=0x30, b=0x6B),
    isBold=True,
    outline=1.5,
    shadow=1.0,
    marginL=113,
    marginR=113,
    marginV=45,
)

REQUIRED_STYLES = [
    DIVIDER_STYLE,
    TITLE_STYLE,
    ROMAJI_STYLE,
    EN_STYLE,
]

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
