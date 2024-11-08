from collections.abc import Sequence, Mapping

from ..ass.to_ass import *
from enum import Enum
from typing import TypeVar
from ..models.karaoke import KObject

import ast
import re
import operator

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
            event.end = kLine.start + kSyl.start + enddelta
        case "presyl":
            event.start = kLine.start + kSyl.start + startdelta
            event.end = kLine.start + kSyl.start + enddelta
        case "syl":
            event.start = kLine.start + kSyl.start + startdelta
            event.end = kLine.start + kSyl.end + enddelta
        case "postsyl":
            event.start = kLine.start + kSyl.end + startdelta
            event.end = kLine.start + kSyl.end + enddelta
        case "syl2end":
            event.start = kLine.start + kSyl.end + startdelta
            event.end = kLine.end + enddelta
        case "postline":
            event.start = kLine.end + startdelta
            event.end = kLine.end + enddelta
        case "start2char":
            event.start = kLine.start + startdelta
            event.end = kLine.start + kChar.start + enddelta
        case "prechar":
            event.start = kLine.start + kChar.start + startdelta
            event.end = kLine.start + kChar.start + enddelta
        case "char":
            event.start = kLine.start + kChar.start + startdelta
            event.end = kLine.start + kChar.end + enddelta
        case "postchar":
            event.start = kLine.start + kChar.end + startdelta
            event.end = kLine.start + kChar.end + enddelta
        case "char2end":
            event.start = kLine.start + kChar.end + startdelta
            event.end = kLine.end + enddelta
        case "syl2char":
            event.start = kLine.start + kSyl.start + startdelta
            event.end = kLine.start + kChar.start + enddelta
        case "char2syl":
            event.start = kLine.start + kChar.end + startdelta
            event.end = kLine.start + kSyl.end + enddelta
        case "sylpct":
            event.start = kLine.start + kSyl.start + (startadjust / 100) * kSyl.duration
            event.end = kLine.start + kSyl.end + (endadjust / 100) * kSyl.duration

    return ""


@dataclass
class Template:
    parts: Sequence[TemplateText]
    templateType: TemplateType

    noblank: bool = False
    notext: bool = False
    repeat: int = 1
    layer: int = 0

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
    def compile(text: str, layer: int = 0) -> Template:
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
            layer=layer,
        )


class TemplateEffect(KaraokeEffect):
    romaji_templates: Sequence[tuple[Template, Range]]
    en_templates: Sequence[tuple[Template, Range]]
    
    romaji_styles: Sequence[tuple[pyass.Style, Range]]
    en_styles: Sequence[tuple[pyass.Style, Range]]

    globals_dict = globals()

    # Supported operations
    ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
    }

    unary_ops = {
        ast.UAdd: operator.pos,  # Unary +
        ast.USub: operator.neg   # Unary -
    }

    @staticmethod
    def _eval_expr(node, kObject: KObject, event: pyass.Event, globals_dict):
        if isinstance(node, ast.BinOp):  # Binary operations
            left = TemplateEffect._eval_expr(node.left, kObject, event, globals_dict)
            right = TemplateEffect._eval_expr(node.right, kObject, event, globals_dict)
            return TemplateEffect.ops[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp):  # Unary operations
            operand = TemplateEffect._eval_expr(node.operand, kObject, event, globals_dict)
            return TemplateEffect.unary_ops[type(node.op)](operand)
        elif isinstance(node, ast.Constant):  # Numbers
            return node.value
        elif isinstance(node, ast.Call):  # Function calls
            func_name = node.func.id
            if func_name in globals_dict and callable(globals_dict[func_name]):
                args = [
                    TemplateEffect._eval_expr(arg, kObject, event, globals_dict) for arg in node.args
                ]
                return globals_dict[func_name](kObject, event, *args)
            else:
                raise NameError(f"Function '{func_name}' is not defined")
        elif isinstance(node, ast.Name):  # Variable lookup
            var_name = node.id
            if var_name in globals_dict:
                return globals_dict[var_name]
            else:
                raise NameError(f"Variable '{var_name}' is not defined")
        elif isinstance(node, ast.Subscript):  # List or dictionary indexing
            value = TemplateEffect._eval_expr(node.value, kObject, event, globals_dict)
            index = TemplateEffect._eval_expr(node.slice.value, kObject, event, globals_dict)
            return value[index]
        elif isinstance(node, ast.Expression):
            return TemplateEffect._eval_expr(node.body, kObject, event, globals_dict)
        else:
            raise TypeError(f"Unsupported type {type(node)}")

    @staticmethod
    def _evaluate_expression(expression, kObject: KObject, event: pyass.Event, globals_dict):
        parsed_expr = ast.parse(expression, mode="eval")
        return TemplateEffect._eval_expr(parsed_expr.body, kObject, event, globals_dict)

    def pick_romaji_style(self, line: int) -> pyass.Style:
        for style, range in self.romaji_styles:
            if range.contains(line):
                return style

    def pick_en_style(self, line: int) -> pyass.Style:
        for style, range in self.en_styles:
            if range.contains(line):
                return style

    @staticmethod
    def _get_function_data(text: str) -> tuple[str, list[str]]:
        node = ast.parse(text, mode="eval")
        function_name = node.body.func.id
        arguments = [ast.literal_eval(arg) for arg in node.body.args]

        return function_name, arguments

    def execute_template(self, template: Template, kObject: KObject) -> pyass.Event:
        event = pyass.Event(
            format=get_line_format(kObject.kLine),
            layer=template.layer,
            start=kObject.start,
            end=kObject.end,
            style=kObject.style.name,
        )

        fullText = ""
        for part in template.parts:
            text = part.get_text(kObject)
            if text.startswith("!"):
                ret = TemplateEffect._evaluate_expression(text[1:-1], kObject, event, self.globals_dict)
                if ret is not None:
                    text = str(ret)
                else:
                    text = ""

            fullText += text
        
        
        if not template.notext:
            fullText += kObject.text

        event.text = fullText
        

        return event

    def apply_templates_to_lines(
        self, songLines: Sequence[KLine]
    ) -> Sequence[pyass.Event]:
        events = []

        for songLine in songLines:
            style = (
                self.pick_en_style(songLine.idxInSong)
                if songLine.isEN
                else self.pick_romaji_style(songLine.idxInSong)
            )
            songLine.style = style
            songLine.transitionDuration = timedelta(milliseconds=500)
            for template, range in self.en_templates if songLine.isEN else self.romaji_templates:
                if range.contains(songLine.idxInSong):
                    if template.templateType == TemplateType.LINE:
                        events.append(self.execute_template(template, songLine))
                    elif template.templateType == TemplateType.SYL:
                        events.extend(
                            self.execute_template(template, syl)
                            for syl in songLine.syls
                            if not template.noblank or len(syl.text.strip()) > 0
                        )
                    elif template.templateType == TemplateType.CHAR:
                        events.extend(
                            self.execute_template(template, char)
                            for char in songLine.chars
                            if not template.noblank or len(char.text.strip()) > 0
                        )

        return events

    def to_romaji_k_events(
        self,
        songLines: Sequence[KLine],
        actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    ) -> Sequence[pyass.Event]:
        return self.apply_templates_to_lines(songLines)

    def to_en_k_events(
        self,
        songLines: Sequence[KLine],
        actorToStyle: Mapping[str, Sequence[pyass.Tag]],
    ) -> Sequence[pyass.Event]:
        return self.apply_templates_to_lines(songLines)


register_effect("template_effect", TemplateEffect())
