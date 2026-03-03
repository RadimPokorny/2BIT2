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
        except (ParseError, etree.XMLSyntaxError):
            raise InterpreterError(ErrorCode.INT_XML, "Invalid XML")
        except ValidationError:
            raise InterpreterError(ErrorCode.INT_STRUCTURE, "Invalid SOL-XML structure")

    def _create_obj(self, class_name: str, value=None):
        """Create object method for a better coding experience."""
        return {"class": class_name, "attrs": {}, "val": value}

    def call_method(self, receiver, selector, args):
        r_cls = receiver.get("class")

        # --- Class constructors ---
        if receiver.get("is_class"):
            if selector == "from:":
                return self._create_obj(r_cls, args[0].get("val"))
            if selector == "new":
                return self._create_obj(r_cls, None)
            raise InterpreterError(ErrorCode.SEM_UNDEF, f"Class {r_cls} does not understand {selector}")

        # --- Object class methods ---
        if selector == "identicalTo:":
            res = (receiver is args[0])
            return self._create_obj("True" if res else "False", res)

        # --- String class methods ---
        if r_cls == "String":
            if selector == "print":
                out = str(receiver.get("val", "")).replace('\\n', '\n').replace('\\t', '\t')
                print(out, end="", flush=True)
                return receiver
            if selector == "asString":
                return receiver

        # --- 3. Native Integer Methods ---
        if r_cls == "Integer" or self._is_subclass(r_cls, "Integer"):
            
            # Arithmetic operator plus
            if selector == "plus:":
                v1, v2 = receiver.get("val", 0), args[0].get("val", 0)
                return self._create_obj("Integer", int(v1) + int(v2))

            # Equation operator
            if selector == "equalTo:":
                res = str(receiver.get("val")) == str(args[0].get("val"))
                return self._create_obj("True" if res else "False", res)

            # Convert to string method
            if selector == "asString":
                return self._create_obj("String", str(receiver.get("val")))

            # Cycle:
            if selector == "timesRepeat:":
                n = int(receiver.get("val", 0))
                block_obj = args[0]
                last_res = self._create_obj("Nil")
                for i in range(1, n + 1):
                    iter_num = self._create_obj("Integer", i)
                    last_res = self.call_method(block_obj, "value:", [iter_num])
                return last_res

        # --- 4. Native Block Methods ---
        if r_cls == "Block":
            if selector.startswith("value"):
                block_data = receiver["val"] 
                block_node = block_data['node']
                captured_self = block_data['captured_self']

                # Arity check
                expected_arity = len(block_node.parameters) if block_node.parameters else 0
                if len(args) != expected_arity:
                    raise InterpreterError(ErrorCode.INT_DNU, f"Block expects {expected_arity} args, got {len(args)}")

                return self.execute_block(block_node, captured_self, args)

        # --- Native Boolean Methods ---
        if r_cls in ["True", "False"]:
            if selector == "ifTrue:ifFalse:":
                block_to_exec = args[0] if r_cls == "True" else args[1]
                # Bloky jsou objekty, musíme je "spustit" přes jejich vnitřní uzel
                return self.call_method(block_to_exec, "value", [])
            if selector == "asString":
                return self._create_obj("String", r_cls.lower())

        # --- Lookup in class hierarchy ---
        curr_name = r_cls
        while curr_name:
            cls_def = self.classes.get(curr_name)
            if not cls_def: break
            method = next((m for m in cls_def.methods if m.selector == selector), None)
            if method:
                return self.execute_block(method.block, receiver, args)
            curr_name = cls_def.parent

        # --- Getters and setters ---
        if selector.endswith(":"):
            attr_name = selector[:-1]
            receiver.setdefault("attrs", {})[attr_name] = args[0]
            return receiver
        if selector in receiver.get("attrs", {}):
            return receiver["attrs"][selector]

        raise InterpreterError(ErrorCode.INT_DNU, f"Method {selector} not found for class {r_cls}")

    def _is_subclass(self, child, parent):
        """Check if 'child' class is a subclass of 'parent' class."""
        
        curr = child
        while curr:
            if curr == parent: return True
            cls_def = self.classes.get(curr)
            curr = cls_def.parent if cls_def else None
        return False

    def evaluate_expr(self, expr_node, variables: dict):
        """Evaluate an expression node and return its value."""
        
        if expr_node.literal:
            lit = expr_node.literal
            if lit.class_id == "class":
                return {"class": lit.value, "is_class": True, "val": lit.value}
            val = int(lit.value) if lit.class_id == "Integer" else lit.value
            return self._create_obj(lit.class_id, val)

        if expr_node.var:
            name = expr_node.var.name
            if name in ["nil", "true", "false"]:
                return self._create_obj(name.capitalize(), (name == "true"))
            if name in variables:
                return variables[name]
            if name in self.classes or name in ["Integer", "String", "Object", "Nil", "True", "False", "Block"]:
                return {"class": name, "is_class": True, "val": name}
            raise InterpreterError(ErrorCode.SEM_UNDEF, f"Variable {name} not defined")

        if expr_node.block:
            # Saving the block node and captured self in the block object for later execution
            block_info = {
                'node': expr_node.block,
                'captured_self': variables.get('self')
            }
            return self._create_obj("Block", block_info)

        if expr_node.send:
            s = expr_node.send
            recv = self.evaluate_expr(s.receiver, variables)
            actual_args = [self.evaluate_expr(a.expr, variables) for a in s.args]
            return self.call_method(recv, s.selector, actual_args)

        return self._create_obj("Nil")

    def execute_block(self, block_node, self_obj, args):
        """Execute a block of code with given self and arguments."""
        
        variables = {"self": self_obj}
        if block_node.parameters:
            for i, p in enumerate(block_node.parameters):
                variables[p.name] = args[i]

        last_v = self._create_obj("Nil")
        for assign in block_node.assigns:
            val = self.evaluate_expr(assign.expr, variables)
            if assign.target.name != "_":
                variables[assign.target.name] = val
            last_v = val
        return last_v

    def execute(self, input_io: TextIO) -> None:
        
        if not self.current_program: return
        self.classes = {cls.name: cls for cls in self.current_program.classes}
        if "Main" not in self.classes:
            raise InterpreterError(ErrorCode.SEM_MAIN, "Main class missing")

        main_inst = self._create_obj("Main")
        self.call_method(main_inst, "run", [])