import re

import pytimeparse

from datetime import timedelta

class Modifier:
    def __init__(self) -> None:
        self.operation = ''
        self.start = None
        self.end = None
        self.rest = []

def parse_modifier(s: str) -> Modifier:
    m = Modifier()

    s = s.removeprefix('(')
    s = s.removesuffix(')')

    parts = s.split(',')
    m.operation = parts[0].lower()

    lineParts = parts[1].split('-')
    if len(lineParts) == 1:
        lineNum = int(lineParts[0])

        m.start = lineNum - 1
        m.end = lineNum
    elif len(lineParts) == 2:
        start, end = lineParts
        m.start = int(start) - 1
        if end:
            m.end = int(end)

    m.rest = parts[2:]

    return m

def parse_modifiers(s: str) -> list[Modifier]:
    return [parse_modifier(match) for match in s.split(';')]

class LineModifier:
    def __init__(self) -> None:
        self.should_force_secondary = False
        self.should_discard = False
        self.offset = timedelta(0)

def to_line_modifiers(modifiers: list[Modifier], maxLines=100) -> list[LineModifier]:
    ret = [LineModifier() for _ in range(maxLines)]

    for modifier in modifiers:
        if modifier.operation == 'discard':
            for i in range(modifier.start, modifier.end if modifier.end is not None else maxLines):
                ret[i].should_discard = True
        elif modifier.operation == 'offset':
            offsetStr = modifier.rest[0]
            offset = timedelta(seconds=pytimeparse.parse(offsetStr))

            for i in range(modifier.start, modifier.end if modifier.end is not None else maxLines):
                ret[i].offset += offset
        elif modifier.operation == 'secondary':
            for i in range(modifier.start, modifier.end if modifier.end is not None else maxLines):
                ret[i].should_force_secondary = True

    return ret

def modify_song(songJson, modifiers: list[Modifier]):
    lineModifiers = to_line_modifiers(modifiers, maxLines=len(songJson['lyrics']['detailed']))

    outDetailedLyrics = []

    for line, modifier in zip(songJson['lyrics']['detailed'], lineModifiers):
        if modifier.should_discard:
            continue

        if modifier.should_force_secondary:
            line['secondary'] = True

        line['start'] = str(timedelta(seconds=pytimeparse.parse(line['start'])) + modifier.offset)
        line['end'] = str(timedelta(seconds=pytimeparse.parse(line['end'])) + modifier.offset)

        outDetailedLyrics.append(line)

    songJson['lyrics']['detailed'] = outDetailedLyrics
    return songJson
