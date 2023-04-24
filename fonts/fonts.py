from collections.abc import Sequence
from functools import cache
import math

from PIL import ImageFont
from matplotlib.font_manager import findSystemFonts

class FontScaler:
    def __init__(self, fontName: str, fontSize: int) -> None:
        self.font = _find_font(fontName, fontSize)

    def split_by_rendered_width(
        self, toSplit: int, text: str, shouldRoundToInteger: bool = True
    ) -> Sequence[float]:
        totalLength = self.font.getlength(text)
        unitVector = [self.font.getlength(c) / totalLength for c in text]

        actualScaledVector = [toSplit * dim for dim in unitVector]
        if not shouldRoundToInteger:
            return actualScaledVector

        ans = [math.floor(f) for f in actualScaledVector]
        decimalPartWithIdx = [
            (f - math.floor(f), i) for i, f in enumerate(actualScaledVector)
        ]
        decimalPartWithIdx.sort(reverse=True)

        missing = toSplit - sum(ans)
        for _, idx in decimalPartWithIdx[:missing]:
            ans[idx] += 1

        return ans

class FontNotFoundException(Exception):
    pass

@cache
def _find_font(fontName: str, fontSize: int) -> ImageFont.FreeTypeFont:
    for font in findSystemFonts():
        try:
            f = ImageFont.FreeTypeFont(font)
            if f.getname()[0] == fontName:
                return ImageFont.truetype(font, fontSize)
        except:
            continue

    raise FontNotFoundException
