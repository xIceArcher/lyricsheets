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
    if s == '':
        return []

    return [parse_modifier(match) for match in s.split(';')]

class LineModifier:
    def __init__(self) -> None:
        self.shouldForceSecondary = False
        self.shouldDiscard = False

        self.offset = timedelta(0)

        self.shouldOverwriteStyle = False
        self.breakpoints = None
        self.actors = None

        self.shouldOverwriteKaraoke = False
        self.start = timedelta(0)
        self.end = timedelta(0)
        self.syllableLengths = []

        self.shouldRunKaraTemplater = False

def to_line_modifiers(modifiers: list[Modifier], maxLines=100) -> list[LineModifier]:
    ret = [LineModifier() for _ in range(maxLines)]

    for modifier in modifiers:
        if modifier.operation == 'discard':
            for i in range(modifier.start, modifier.end if modifier.end is not None else maxLines):
                ret[i].shouldDiscard = True
        elif modifier.operation == 'offset':
            offsetStr = modifier.rest[0]
            offset = timedelta(seconds=pytimeparse.parse(offsetStr))

            for i in range(modifier.start, modifier.end if modifier.end is not None else maxLines):
                ret[i].offset += offset
        elif modifier.operation == 'secondary':
            for i in range(modifier.start, modifier.end if modifier.end is not None else maxLines):
                ret[i].shouldForceSecondary = True
        elif modifier.operation == 'style':
            if len(modifier.rest) == 1 and not ':' in modifier.rest[0]:
                # Simple case, entire line is the same actor
                actor = int(modifier.rest[0])
                for i in range(modifier.start, modifier.end if modifier.end is not None else maxLines):
                    ret[i].shouldOverwriteStyle = True
                    ret[i].breakpoints = [0]
                    ret[i].actors = [actor]
            else:
                breakpoints = []
                actors = []

                for breakpointToActorStr in modifier.rest:
                    breakpoint, actor = breakpointToActorStr.split(':')
                    breakpoints.append(int(breakpoint) - 1)
                    actors.append(int(actor))

                for i in range(modifier.start, modifier.end if modifier.end is not None else maxLines):
                    ret[i].shouldOverwriteStyle = True
                    ret[i].breakpoints = breakpoints
                    ret[i].actors = actors
        elif modifier.operation == 'karaoke':
            ret[modifier.start].shouldOverwriteKaraoke = True
            ret[modifier.start].start = timedelta(seconds=pytimeparse.parse(modifier.rest[0]))
            ret[modifier.start].end = timedelta(seconds=pytimeparse.parse(modifier.rest[1]))
            ret[modifier.start].syllableLengths = modifier.rest[2:]
        elif modifier.operation == 'templater':
            ret[0].shouldRunKaraTemplater = True
        

    return ret

def modify_song(songJson, modifiers: list[Modifier]):
    lineModifiers = to_line_modifiers(modifiers, maxLines=len(songJson['lyrics']['detailed']))
    shouldRunKaraTemplater = False
    outDetailedLyrics = []

    for line, modifier in zip(songJson['lyrics']['detailed'], lineModifiers):
        if modifier.shouldDiscard:
            continue

        if modifier.shouldForceSecondary:
            line['secondary'] = True

        if modifier.shouldOverwriteKaraoke:
            line['start'] = str(modifier.start + modifier.offset)
            line['end'] = str(modifier.end + modifier.offset)
            for syllable, newTime in zip(line['syllables'], modifier.syllableLengths):
                syllable['len'] = int(newTime)
        else:
            line['start'] = str(timedelta(seconds=pytimeparse.parse(line['start'])) + modifier.offset)
            line['end'] = str(timedelta(seconds=pytimeparse.parse(line['end'])) + modifier.offset)

        if modifier.shouldOverwriteStyle:
            line['breakpoints'] = modifier.breakpoints
            line['actors'] = modifier.actors

        if modifier.shouldRunKaraTemplater:
            shouldRunKaraTemplater = True

        outDetailedLyrics.append(line)

    songJson['lyrics']['detailed'] = outDetailedLyrics
    songJson['templater'] = shouldRunKaraTemplater
    return songJson
