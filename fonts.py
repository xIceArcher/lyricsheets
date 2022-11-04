import math
from PIL import ImageFont

def get_char_proportions_by_font_width(text: str, fontName: str, fontSize: int):
    font = ImageFont.truetype(fontName, fontSize)
    totalLength = font.getlength(text)
    return [font.getlength(c) / totalLength for c in text]

def scale_and_round_unit_vector_preserving_sum(scale: int, unitVector: list[float]):
    actualScaledVector = [scale * dim for dim in unitVector]

    ans = [math.floor(f) for f in actualScaledVector]
    decimalPartWithIdx = [(f - math.floor(f), i) for i, f in enumerate(actualScaledVector)]
    decimalPartWithIdx.sort(reverse=True)

    missing = scale - sum(ans)
    for _, idx in decimalPartWithIdx[:missing]:
        ans[idx] += 1

    return ans
