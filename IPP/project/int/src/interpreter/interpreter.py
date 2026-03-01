import logging
from pathlib import Path
from typing import TextIO

from lxml import etree
from lxml.etree import ParseError
from pydantic import ValidationError

from .error_codes import ErrorCode
from .exceptions import InterpreterError
from .input_model import Program

logger = logging.getLogger(__name__)


class Interpreter:
    def __init__(self) -> None:
        self.current_program: Program | None = None
        self.classes: dict = {}

    def load_program(self, source_file_path: Path) -> None:
        try:
            xml_tree = etree.parse(source_file_path)
            self.current_program = Program.from_xml_tree(xml_tree.getroot())
        except ParseError:
            raise InterpreterError(ErrorCode.INT_XML, "Invalid XML")
        except ValidationError:
            raise InterpreterError(ErrorCode.INT_STRUCTURE, "Invalid SOL-XML structure")

    def call_method(self, receiver, selector, args):
        # --- Třída String ---
        if receiver["class"] == "String":
            if selector == "print":
                # Specifikace 2: Vytiskne řetězec bez formátovacích znaků
                print(str(receiver["val"]), end="", flush=True)
                # Specifikace 2: Vrací self
                return receiver
            if selector == "asInteger":
                try:
                    return {"class": "Integer", "attrs": {}, "val": int(receiver["val"])}
                except:
                    return {"class": "Nil", "attrs": {}, "val": None}
            if selector == "asString":
                return receiver

        # --- Třída Integer ---
        if receiver["class"] == "Integer":
            if selector == "plus:":
                res = int(receiver["val"]) + int(args[0]["val"])
                return {"class": "Integer", "attrs": {}, "val": res}
            if selector == "asString":
                return {"class": "String", "attrs": {}, "val": str(receiver["val"])}

        # --- Podmínky (ifTrue:ifFalse:) ---
        if receiver["class"] in ["True", "False"]:
            if selector == "ifTrue:ifFalse:":
                # args[0] je blok pro True, args[1] pro False
                chosen_block_obj = args[0] if receiver["class"] == "True" else args[1]
                # Spustíme vnitřek bloku (v modelu je to pod .val)
                return self.execute_block(chosen_block_obj["val"], receiver, [])

        # --- Standardní Lookup ---
        curr_name = receiver["class"]
        method_def = None
        while curr_name:
            curr_def = self.classes.get(curr_name)
            if not curr_def: break
            found = next((m for m in curr_def.methods if m.selector == selector), None)
            if found:
                method_def = found
                break
            curr_name = curr_def.parent

        if not method_def:
            # Gettery / Settery
            if selector.endswith(":"):
                receiver["attrs"][selector[:-1]] = args[0]
                return receiver
            elif selector in receiver["attrs"]:
                return receiver["attrs"][selector]
            raise InterpreterError(ErrorCode.INT_DNU, f"Method {selector} not found")

        return self.execute_block(method_def.block, receiver, args)

    def evaluate_expr(self, expr_node, variables: dict):
        if expr_node.literal:
            return {"class": expr_node.literal.class_id, "attrs": {}, "val": expr_node.literal.value}

        if expr_node.var:
            name = expr_node.var.name
            if name in ["nil", "true", "false"]:
                # Mapujeme SOL názvy na naše třídy
                cls = name.capitalize()
                return {"class": cls, "attrs": {}, "val": (name == "true")}
            if name in variables: return variables[name]
            raise InterpreterError(ErrorCode.SEM_UNDEF, f"Var {name} undef")

        if expr_node.block:
            # TADY JE ZMĚNA: Blok nevykonáme, ale zabalíme ho jako objekt "Block"
            # aby se dal předat do ifTrue:ifFalse:
            return {"class": "Block", "attrs": {}, "val": expr_node.block}

        if expr_node.send:
            s = expr_node.send
            # Rekurzivní vyhodnocení (vnořené zprávy)
            recv = self.evaluate_expr(s.receiver, variables)
            actual_args = [self.evaluate_expr(a.expr, variables) for a in s.args]
            return self.call_method(recv, s.selector, actual_args)

        return {"class": "Nil", "attrs": {}, "val": None}

    def execute_block(self, block_node, self_obj, args):
        # Parametry bloku jsou v variables od začátku
        variables = {"self": self_obj}
        if block_node.parameters:
            for i, p in enumerate(block_node.parameters):
                variables[p.name] = args[i]

        last_value = {"class": "Nil", "attrs": {}, "val": None}

        # SOL26: sekvence PŘÍKAZŮ PŘIŘAZENÍ
        for assign in block_node.assigns:
            # 1. Vyhodnotíme pravou stranu (výraz)
            val = self.evaluate_expr(assign.expr, variables)

            # 2. Uložíme do levé strany (target)
            target_name = assign.target.name
            if target_name != '_':  # Podle 1.1 specifikace se do '_' sice přiřazuje, ale dál se nepoužívá
                variables[target_name] = val

            # 3. Zapamatujeme si poslední hodnotu pro návrat z bloku (sekce 1.2.6)
            last_value = val

        return last_value

    def execute(self, input_io: TextIO) -> None:
        if not self.current_program: return
        self.classes = {cls.name: cls for cls in self.current_program.classes}

        if "Main" not in self.classes:
            raise InterpreterError(ErrorCode.SEM_MAIN, "Main class missing")

        main_instance = {"class": "Main", "attrs": {}, "val": None}
        self.call_method(main_instance, "run", [])