from collections.abc import Sequence, Mapping

from ..ass.to_ass import *
from enum import Enum
from typing import TypeVar
from ..models.karaoke import KObject

import ast
import re

Template = TypeVar("Template", bound="Template")

inlinePattern = re.compile(r"(\$[a-zA-Z]+)")
codePattern = re.compile(r"(![^!]+!)")


class TemplateType(Enum):
    LINE = 1
    PRELINE = 2
    SYL = 3
    CHAR = 4


@dataclass
class Range:
    ranges: Sequence[tuple[int, int]]

    def __init__(self, *ranges: Sequence[tuple[int, int]]):
        self.ranges = []
        for r in ranges:
            if isinstance(r, tuple) and len(r) == 2:
                start, end = r
                if start <= end:
                    self.ranges.append((start, end))
                else:
                    raise ValueError(
                        "Range start must be less than or equal to range end"
                    )
            else:
                raise ValueError("Each range must be a tuple (start, end)")

    def contains(self, number: int) -> bool:
        # Check if the number falls within any of the defined ranges
        for start, end in self.ranges:
            if start <= number <= end:
                return True
        return False


@dataclass
class TemplateText:
    parts: Sequence[str]

    def _inline(self, part: str, kObject: KObject) -> str:
        return str(kObject.inline_var(part[1:])) if part.startswith("$") else part

    def get_text(self, kObject: KObject) -> str:
        return "".join(self._inline(part, kObject) for part in self.parts)


def retime(
    kObject: KObject,
    event: pyass.Event,
    mode: str,
    startadjust: int,
    endadjust: int,
):
    kLine = kObject.kLine
    kSyl = kObject.kSyl
    kChar = kObject.kChar

    startdelta = timedelta(milliseconds=startadjust)
    enddelta = timedelta(milliseconds=endadjust)

    match mode:
        case "abs" | "set":
            event.start = startdelta
            event.end = enddelta
        case "preline":
            event.start = kLine.start + startdelta
            event.end = kLine.start + enddelta
        case "line":
            event.start = kLine.start + startdelta
            event.end = kLine.end + enddelta
        case "start2syl":
            event.start = kLine.start + startdelta
            event.end = kSyl.start + enddelta
        case "presyl":
            event.start = kSyl.start + startdelta
            event.end = kSyl.start + enddelta
        case "syl":
            event.start = kSyl.start + startdelta
            event.end = kSyl.end + enddelta
        case "postsyl":
            event.start = kSyl.end + startdelta
            event.end = kSyl.end + enddelta
        case "syl2end":
            event.start = kSyl.end + startdelta
            event.end = kLine.end + enddelta
        case "postline":
            event.start = kLine.end + startdelta
            event.end = kLine.end + enddelta
        case "start2char":
            event.start = kLine.start + startdelta
            event.end = kChar.start + enddelta
        case "prechar":
            event.start = kChar.start + startdelta
            event.end = kChar.start + enddelta
        case "char":
            event.start = kChar.start + startdelta
            event.end = kChar.end + enddelta
        case "postchar":
            event.start = kChar.end + startdelta
            event.end = kChar.end + enddelta
        case "char2end":
            event.start = kChar.end + startdelta
            event.end = kLine.end + enddelta
        case "syl2char":
            event.start = kSyl.start + startdelta
            event.end = kChar.start + enddelta
        case "char2syl":
            event.start = kChar.end + startdelta
            event.end = kSyl.end + enddelta
        case "sylpct":
            event.start = kSyl.start + (startadjust / 100) * kSyl.duration
            event.end = kSyl.end + (endadjust / 100) * kSyl.duration

    return ""


@dataclass
class Template:
    parts: Sequence[TemplateText]
    templateType: TemplateType

    noblank: bool = False
    notext: bool = False
    repeat: int = 1

    @staticmethod
    def _split_code(text: str) -> Sequence[str]:
        split = [sp for sp in codePattern.split(text) if len(sp) > 0]
        return split

    @staticmethod
    def _split_inline(text: str) -> TemplateText:
        split = TemplateText(
            parts=[
                part.lower() if part.startswith("$") else part
                for part in inlinePattern.split(text)
                if len(part) > 0
            ]
        )
        return split

    @staticmethod
    def compile(text: str) -> Template:
        templates = text.split(":")
        pretext = templates[0].lower().split(" ")
        template_text = templates[1].strip()

        if "char" in pretext:
            template_type = TemplateType.CHAR
        elif "pre-line" in pretext:
            template_type = TemplateType.PRELINE
        elif "line" in pretext:
            template_type = TemplateType.LINE
        elif "syl" in pretext:
            template_type = TemplateType.SYL
        else:
            template_type = TemplateType.SYL

        repeat = 1
        for i, x in enumerate(pretext):
            if x == "repeat" or x == "loop":
                repeat = int(pretext[i + 1])
                break

        return Template(
            parts=[
                Template._split_inline(code_segment)
                for code_segment in Template._split_code(template_text)
            ],
            templateType=template_type,
            noblank="noblank" in pretext,
            notext="notext" in pretext,
            repeat=repeat,
        )


class TemplateEffect(KaraokeEffect):
    templates: Sequence[tuple[Template, Range]]
    styles: Sequence[tuple[pyass.Style, Range]]

    @staticmethod
    def _get_function_data(text: str) -> tuple[str, list[str]]:
        node = ast.parse(text, mode="eval")
        function_name = node.body.func.id
        arguments = [ast.literal_eval(arg) for arg in node.body.args]

        return function_name, arguments

    def execute_template(self, template: Template, kObject: KObject) -> pyass.Event:
        event = pyass.Event(
            format=get_line_format(kObject.kLine),
            layer=0,
            start=kObject.start,
            end=kObject.end,
            style="",
        )

        fullText = ""
        for part in template.parts:
            text = part.get_text(kObject)
            if text.startswith("!"):
                function_name, arguments = self._get_function_data(text[1:-1])

                fn = globals().get(function_name)
                if callable(fn):
                    ret = fn(kObject, event, *arguments)
                    if ret is not None:
                        text = ret
                    else:
                        text = ""

            fullText += text

        event.text = fullText

        return event

    def apply_templates_to_lines(
        self, songLines: Sequence[KLine]
    ) -> Sequence[pyass.Event]:
        events = []

        for songLine in songLines:
            for template, range in self.templates:
                if range.contains(songLine.idxInSong):
                    if template.templateType == TemplateType.LINE:
                        events.append(self.execute_template(template, songLine))
                    elif template.templateType == TemplateType.SYL:
                        events.extend(
                            self.execute_template(template, syl)
                            for syl in songLine.syls
                        )
                    elif template.templateType == TemplateType.CHAR:
                        events.extend(
                            self.execute_template(template, char)
                            for char in songLine.chars
                        )

        return events

    def to_romaji_k_events(
        self,
        songLines: Sequence[KLine],
        actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    ) -> Sequence[pyass.Event]:
        pass

    def to_en_k_events(
        self,
        songLines: Sequence[KLine],
        actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    ) -> Sequence[pyass.Event]:
        pass


register_effect("template_effect", TemplateEffect())
