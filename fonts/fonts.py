from collections.abc import Sequence
import math

from PIL import ImageFont


class FontScaler:
    def __init__(self, fontName: str, fontSize: int) -> None:
        self.font = ImageFont.truetype(fontName, fontSize)

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
