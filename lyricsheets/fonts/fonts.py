from collections.abc import Sequence
from functools import cache
import math

from pyass import Style
import wx

_ = wx.App()
PRECISION_SCALE = 64


class FontScaler:
    def __init__(self, style: Style):
        self.dc = wx.MemoryDC()
        self.dc.SetFont(_find_font(style))
        self.style = style

    def split_by_rendered_width(
        self, toSplit: int, text: str, shouldRoundToInteger: bool = True
    ) -> Sequence[float]:
        vector = [self.dc.GetTextExtent(c).width for c in text]
        totalLength = sum(vector)
        unitVector = [dim / totalLength for dim in vector]

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

    def get_length(self, text: str) -> float:
        width = 0
        if self.style.spacing:
            for c in text:
                extent = self.dc.GetTextExtent(c)
                scaling = (
                    self.style.fontSize
                    * PRECISION_SCALE
                    / (extent.height if extent.height > 0 else 1)
                )
                width += (extent.width + self.style.spacing) * scaling
        else:
            extent = self.dc.GetTextExtent(text)
            scaling = (
                self.style.fontSize
                * PRECISION_SCALE
                / (extent.height if extent.height > 0 else 1)
            )
            width = extent.width * scaling

        return self.style.scaleX / 100 * width / PRECISION_SCALE


def _find_font(style: Style) -> wx.Font:
    return _find_font_cached(
        style.fontName,
        style.fontSize,
        style.isBold,
        style.isItalic,
        style.isUnderline,
        style.isStrikeout,
    )


@cache
def _find_font_cached(
    fontName: str,
    fontSize: int,
    isBold: bool,
    isItalic: bool,
    isUnderline: bool,
    isStrikethrough: bool,
) -> wx.Font:
    return wx.Font(
        wx.FontInfo(fontSize * PRECISION_SCALE)
        .FaceName(fontName)
        .Family(wx.FONTFAMILY_DEFAULT)
        .Bold(isBold)
        .Italic(isItalic)
        .Underlined(isUnderline)
        .Strikethrough(isStrikethrough)
        .Encoding(wx.FONTENCODING_SYSTEM)
    )
