def get_row(cellRef: str) -> int:
    for i in range(len(cellRef)):
        try:
            return int(cellRef[i:])
        except ValueError:
            continue

def get_row_idx(cellRef: str) -> int:
    return get_row(cellRef) - 1

def get_column(cellRef: str) -> str:
    row = str(get_row(cellRef))
    return cellRef[:len(cellRef)-len(row)]

def get_column_idx(cellRef: str) -> int:
    col = get_column(cellRef)
    ret = -1
    for i, c in enumerate(col[::-1]):
        cVal = ord(c) - ord('A') + 1
        ret += cVal * (26 ** i)

    return ret
