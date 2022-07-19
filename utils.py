def get_row(cellRef: str) -> int:
    for i in range(len(cellRef)):
        try:
            return int(cellRef[i:])
        except ValueError:
            continue

def get_row_idx(cellRef: str) -> int:
    return get_row(cellRef) - 1

def get_column(cellRef: str) -> str:
    row = get_row(cellRef)
    if row is None:
        return cellRef

    return cellRef[:len(cellRef)-len(str(row))]

def get_column_idx(cellRef: str) -> int:
    col = get_column(cellRef)
    ret = -1
    for i, c in enumerate(col[::-1]):
        cVal = ord(c) - ord('A') + 1
        ret += cVal * (26 ** i)

    return ret

def color_to_hex(color) -> str:
    r = round(color['red'] * 255) if 'red' in color else 0
    g = round(color['green'] * 255) if 'green' in color else 0
    b = round(color['blue'] * 255) if 'blue' in color else 0

    return f'{r:02x}{g:02x}{b:02x}'

def is_white(color) -> bool:
    return 'red' in color and color['red'] == 1 and 'green' in color and color['green'] == 1 and 'blue' in color and color['blue'] == 1
