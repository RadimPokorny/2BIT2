"""
This module contains the main logic of the interpreter.

IPP: You must definitely modify this file. Bend it to your will.

Author: Ondřej Ondryáš <iondryas@fit.vut.cz>
Author:
"""

import logging
from pathlib import Path
from typing import Any, TextIO

from lxml import etree
from lxml.etree import ParseError
from pydantic import ValidationError

from .error_codes import ErrorCode
from .exceptions import InterpreterError
from .input_model import Program

logger = logging.getLogger(__name__)


class Environment:
    """
    The main environment of the interpreter.
    """

    def __init__(self, parent=None):
        self.values: dict = {}
        self.parent: Environment = parent
        self.params: set = set()  # Error 34 handle (assign to the parameter)

    def lookup(self, name: str):
        """Lookup for the variable by name in current and parent scopes."""
        if name in self.values:
            return self.values[name]
        if self.parent:
            return self.parent.lookup(name)
        # If no variable is found, throw error 32 (uninitialized/undefined)
        raise InterpreterError(ErrorCode.SEM_UNDEF, f"Variable {name} not defined")

    def assign(self, name: str, value):
        """Update an existing variable in the scope or create a new one in the current scope."""
        # Check if we are trying to assign to a formal parameter (Error 34)
        curr = self
        while curr:
            if name in curr.values:
                if name in curr.params:
                    raise InterpreterError(
                        ErrorCode.SEM_COLLISION, f"Cannot assign to parameter {name}"
                    )
                curr.values[name] = value
                return
            curr = curr.parent

        # If variable does not exist in any parent scope, create it in the current scope
        self.values[name] = value


class Interpreter:
    """
    The main interpreter class, responsible for loading the source file and executing the program.
    """

    def __init__(self) -> None:
        self.current_program: Program | None = None
        self.classes: dict = {}
        # Useful skeletons
        self.nil_obj = {"class": "Nil", "attrs": {}, "val": None}
        self.true_obj = {"class": "True", "attrs": {}, "val": True}
        self.false_obj = {"class": "False", "attrs": {}, "val": False}

    def load_program(self, source_file_path: Path) -> None:
        """
        Reads the source SOL-XML file and stores it as the target program for this interpreter.
        If any program was previously loaded, it is replaced by the new one.

        IPP: If you wish to run static checks on the program before execution, this is a good place
             to call them from.
        """
        try:
            xml_tree = etree.parse(source_file_path)
        except ParseError as e:
            raise InterpreterError(
                error_code=ErrorCode.INT_XML, message="Error parsing input XML"
            ) from e
        try:
            self.current_program = Program.from_xml_tree(xml_tree.getroot())  # type: ignore
        except ValidationError as e:
            raise InterpreterError(
                error_code=ErrorCode.INT_STRUCTURE, message="Invalid SOL-XML structure"
            ) from e

    def _create_obj(self, class_name: str, value=None):
        """Create object method"""
        if class_name == "Nil":
            return self.nil_obj
        if class_name == "True":
            return self.true_obj
        if class_name == "False":
            return self.false_obj
        return {"class": class_name, "attrs": {}, "val": value}

    def _find_method(self, start_class_name, selector):
        """We need to find a method by name in the class hierarchy."""
        curr_name = start_class_name
        while curr_name:
            cls_def = self.classes.get(curr_name)
            if not cls_def:
                break
            method = next((m for m in cls_def.methods if m.selector == selector), None)
            if method:
                return method, curr_name
            curr_name = cls_def.parent
        return None, None

    def _is_subclass(self, child, parent):
        """Check if 'child' class is a subclass of 'parent' class."""
        curr = child
        while curr:
            if curr == parent:
                return True
            cls_def = self.classes.get(curr)
            curr = cls_def.parent if cls_def else None
        return False

    def _handle_static_methods(self, r_cls, selector, args):
        """
        Handles messages sent to class objects, such as object creation or static reading.
        """
        if selector == "from:":
            source_obj = args[0]
            source_val = source_obj.get("val")
            needs_val = (
                    r_cls == "Integer"
                    or self._is_subclass(r_cls, "Integer")
                    or r_cls == "String"
                    or r_cls == "Block"
            )
            if needs_val and source_val is None:
                raise InterpreterError(
                    ErrorCode.INT_INVALID_ARG,
                    f"Source object lacks internal value for {r_cls}",
                )
            new_obj = self._create_obj(r_cls, source_val)
            new_obj["attrs"] = source_obj.get("attrs", {}).copy()
            return new_obj
        if selector == "new":
            if r_cls == "Nil":
                return self.nil_obj
            if r_cls == "Block":
                from unittest.mock import MagicMock
                dummy_node = MagicMock(parameters=[], assigns=[])
                return self._create_obj(
                    "Block",
                    {
                        "node": dummy_node,
                        "captured_env": Environment(),
                        "defining_class": None,
                    },
                )
            return self._create_obj(r_cls, None)
        if r_cls == "String" and selector == "read":
            import sys
            line = sys.stdin.readline()
            if not line:
                return self._create_obj("String", "")
            return self._create_obj("String", line.rstrip("\n"))
        raise InterpreterError(ErrorCode.SEM_UNDEF,
                               f"Class {r_cls} does not understand {selector}")

    def _handle_universal_methods(self, receiver, r_cls, selector, args):
        """
        Handles identity checks and type-querying methods common to all objects.
        """
        if selector == "identicalTo:":
            res = receiver is args[0]
            return self._create_obj("True" if res else "False", res)
        if selector == "equalTo:":
            val1 = receiver.get("val")
            val2 = args[0].get("val")
            res = receiver is args[0] if r_cls in ["Nil", "True", "False"] else val1 == val2
            return self._create_obj("True" if res else "False", res)
        type_checks = {
            "isNumber": (r_cls == "Integer" or self._is_subclass(r_cls, "Integer")),
            "isString": (r_cls == "String"),
            "isBlock": (r_cls == "Block"),
            "isNil": (r_cls == "Nil"),
            "isBoolean": (r_cls in ["True", "False"]),
        }
        if selector in type_checks:
            res = type_checks[selector]
            return self._create_obj("True" if res else "False", res)
        return None

    def _handle_string_methods(self, receiver, selector, args):
        """
        Processes methods specific to the String class using a dispatch table.
        """
        # Map selector names to private handler methods
        handlers = {
            "print": self._string_print,
            "length": self._string_length,
            "concatenateWith:": self._string_concatenate,
            "startsWith:endsBefore:": self._string_slice,
            "asString": lambda r, a: r,
            "asInteger": self._string_as_int
        }

        if selector in handlers:
            return handlers[selector](receiver, args)

        return None

    def _string_print(self, receiver, args):
        """Prints the string with escaped characters handled."""
        val = str(receiver.get("val", ""))
        out = val.replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\")
        print(out, end="", flush=True)
        return receiver

    def _string_length(self, receiver, args):
        """Returns the length of the string after unicode decoding."""
        s_val = str(receiver.get("val", ""))
        processed_val = s_val.encode("utf-8").decode("unicode_escape")
        return self._create_obj("Integer", len(processed_val))

    def _string_concatenate(self, receiver, args):
        """Concatenates two strings if types match."""
        arg_cls = args[0].get("class")
        if arg_cls == "String" or self._is_subclass(arg_cls, "String"):
            return self._create_obj("String",
                                    str(receiver.get("val", "")) +
                                    str(args[0].get("val", "")))
        return self.nil_obj

    def _string_slice(self, receiver, args):
        """Handles the startsWith:endsBefore: slicing logic."""
        s_val = str(receiver.get("val", ""))
        try:
            start_idx, end_idx = int(args[0].get("val", 0)), int(args[1].get("val", 0))
            if start_idx <= 0 or end_idx <= 0:
                return self.nil_obj
            if (end_idx - start_idx) <= 0:
                return self._create_obj("String", "")
            return self._create_obj("String", s_val[start_idx - 1: end_idx - 1])
        except (ValueError, TypeError):
            return self.nil_obj

    def _string_as_int(self, receiver, args):
        """Converts string value to an integer object."""
        try:
            return self._create_obj("Integer", int(receiver.get("val", 0)))
        except (ValueError, TypeError):
            return self.nil_obj

    def _handle_integer_methods(self, receiver, selector, args):
        """
        Processes methods specific to the Integer class and its subclasses using a dispatch table.
        """
        handlers = {
            "divBy:": self._int_div,
            "asString": self._int_as_string,
            "asInteger": lambda r, a: r,
            "plus:": self._int_arithmetic,
            "minus:": self._int_arithmetic,
            "multiplyBy:": self._int_arithmetic,
            "greaterThan:": self._int_arithmetic,
            "timesRepeat:": self._int_times_repeat,
        }

        if selector in handlers:
            return handlers[selector](receiver, selector, args)
        return None

    def _int_div(self, receiver, selector, args):
        """Handles integer division with zero-check."""
        argval2 = args[0].get("val", 0)
        if argval2 == 0:
            raise InterpreterError(ErrorCode.INT_INVALID_ARG, "Division by zero")
        return self._create_obj("Integer", receiver.get("val", 0) // argval2)

    def _int_as_string(self, receiver, selector, args):
        """Converts integer value to a string object."""
        return self._create_obj("String", str(receiver.get("val", 0)))

    def _int_arithmetic(self, receiver, selector, args):
        """Handles basic arithmetic and comparison for integers."""
        arg = args[0]
        if not (arg.get("class") == "Integer" or self._is_subclass(arg.get("class"), "Integer")):
            raise InterpreterError(ErrorCode.INT_OTHER,
                                   f"Operand for {selector} must be an Integer")

        v1, v2 = receiver.get("val", 0), arg.get("val", 0)

        if selector == "plus:":
            return self._create_obj("Integer", v1 + v2)
        if selector == "minus:":
            return self._create_obj("Integer", v1 - v2)
        if selector == "multiplyBy:":
            return self._create_obj("Integer", v1 * v2)
        if selector == "greaterThan:":
            return self._create_obj("True" if v1 > v2 else "False", v1 > v2)
        return None

    def _int_times_repeat(self, receiver, selector, args):
        """Executes a block N times, where N is the receiver's value."""
        n = int(receiver.get("val", 0))
        last_res = self.nil_obj
        block = args[0]
        # Does block have a parameters?
        has_p = len(block.get("val", {}).get("node").parameters or []) > 0

        for i in range(1, n + 1):
            if has_p:
                last_res = self.call_method(block, "value:", [self._create_obj("Integer", i)])
            else:
                last_res = self.call_method(block, "value", [])
        return last_res

    def _handle_block_methods(self, receiver, selector, args):
        """
        Processes methods specific to the Block class, including execution and loops.
        """
        if selector.startswith("value"):
            data = receiver["val"]
            if not data or "node" not in data:
                return self.nil_obj
            if len(args) != len(data["node"].parameters or []):
                raise InterpreterError(ErrorCode.SEM_ARITY, "Wrong number of arguments for block")
            return self.execute_block(data["node"], args, data["captured_env"],
                                      defining_class=data.get("defining_class"))
        if selector == "whileTrue:":
            body, last_res = args[0], self.nil_obj
            while self.call_method(receiver, "value", []) is self.true_obj:
                last_res = self.call_method(body, "value", [])
            return last_res
        return None

    def _handle_boolean_nil_methods(self, r_cls, selector, args):
        """
        Processes methods specific to Boolean (True/False) and Nil classes.
        """
        if r_cls in ["True", "False"]:
            if selector == "not":
                return self.false_obj if r_cls == "True" else self.true_obj
            if selector == "and:":
                return self.false_obj if r_cls == "False" else self.call_method(args[0],
                                                                                "value", [])
            if selector == "ifTrue:":
                return self.call_method(args[0], "value", []) if r_cls == "True" else self.nil_obj
            if selector == "ifFalse:":
                return self.call_method(args[0], "value",
                                                               []) \
                                        if r_cls == "False" else self.nil_obj
            if selector == "or:":
                return self.true_obj if r_cls == "True" else self.call_method(args[0], "value", [])
            if selector == "ifTrue:ifFalse:":
                return self.call_method(args[0] if r_cls == "True" else args[1], "value",
                                                                      [])
            if selector == "asString":
                return self._create_obj("String", r_cls.lower())
        if r_cls == "Nil" and selector == "asString":
            return self._create_obj("String", "nil")
        return None

    def _handle_builtin_specializations(self, receiver, r_cls, selector, args):
        """
        Dispatches logic for built-in types to specialized handler methods.
        """
        if r_cls == "String":
            res = self._handle_string_methods(receiver, selector, args)
            if res is not None:
                return res

        if r_cls == "Integer" or self._is_subclass(r_cls, "Integer"):
            res = self._handle_integer_methods(receiver, selector, args)
            if res is not None:
                return res

        if r_cls == "Block" or self._is_subclass(r_cls, "Block"):
            res = self._handle_block_methods(receiver, selector, args)
            if res is not None:
                return res

        # Handle True, False, and Nil
        res = self._handle_boolean_nil_methods(r_cls, selector, args)
        if res is not None:
            return res

        return None

    def _handle_attribute_access(self, receiver, selector, args, start_lookup):
        """
        Handles dynamic attribute access including getters and setters with collision checks.
        """
        if selector.endswith(":"):
            attr_name = selector[:-1]
            collision, _ = self._find_method(start_lookup, attr_name)
            if collision:
                raise InterpreterError(ErrorCode.INT_INST_ATTR,
                                       f"Error 54: Collision with method {attr_name}")
            receiver.setdefault("attrs", {})[attr_name] = args[0]
            return receiver
        if selector in receiver.get("attrs", {}):
            return receiver["attrs"][selector]
        if selector == "asString":
            return self._create_obj("String", "")
        return None

    def call_method(self, receiver, selector, args, defining_class=None, use_super=False):
        """Global function to handle the methods in the program"""
        if isinstance(receiver, dict) and receiver.get("_is_super_wrapper"):
            use_super = True
            receiver = receiver["_inner_obj"]

        r_cls = receiver.get("class")
        if r_cls == "Block" and defining_class is None:
            defining_class = receiver.get("val", {}).get("defining_class")

        # --- 1. Class-level messages (Constructors & Static) ---
        if receiver.get("is_class"):
            return self._handle_static_methods(r_cls, selector, args)

        # --- 2. Universal Object methods (Section 2) ---
        res = self._handle_universal_methods(receiver, r_cls, selector, args)
        if res is not None:
            return res

        # --- 3. Built-in Class Specializations ---
        res = self._handle_builtin_specializations(receiver, r_cls, selector, args)
        if res is not None:
            return res

        # --- 4. User-defined Method Lookup ---
        start_lookup = r_cls
        if use_super:
            ctx_class = self.classes.get(defining_class)
            if ctx_class and ctx_class.parent:
                start_lookup = ctx_class.parent
            else:
                raise InterpreterError(ErrorCode.INT_DNU, f"Super method {selector} not found")

        method, method_class = self._find_method(start_lookup, selector)
        if method:
            method_env = Environment()
            method_env.values["self"] = receiver
            return self.execute_block(method.block, args, method_env, defining_class=method_class)

        # --- 5. Attribute access (Getters/Setters) ---
        res = self._handle_attribute_access(receiver, selector, args, start_lookup)
        if res is not None:
            return res

        # If everything fails: Does Not Understand
        raise InterpreterError(ErrorCode.INT_DNU, f"Method {selector} not found for class {r_cls}")

    def _resolve_variable_name(self, name: str, env: Environment) -> Any:
        """
        Resolves a variable name to its corresponding object, handling keywords,
        special variables like self/super, and class identifiers.
        """
        # Simple constants
        constants = {
            "nil": self.nil_obj,
            "true": self.true_obj,
            "false": self.false_obj,
        }
        if name in constants:
            return constants[name]

        if name == "self":
            return env.lookup("self")

        if name == "super":
            obj = env.lookup("self")
            return {"_is_super_wrapper": True, "_inner_obj": obj}

        # Check if we know the object name
        builtin_classes = {"Integer", "String", "Object", "Nil", "True", "False", "Block"}
        if name in self.classes or name in builtin_classes:
            return {"class": name, "is_class": True, "val": name}

        # We need to lookup
        return env.lookup(name)

    def evaluate_expr(self, expr_node, env: Environment, defining_class=None):
        """Evaluate an expression node and return its value within the given environment."""
        if expr_node.literal:
            lit = expr_node.literal
            if lit.class_id == "class":
                return {"class": lit.value, "is_class": True, "val": lit.value}
            val = int(lit.value) if lit.class_id == "Integer" else lit.value
            return self._create_obj(lit.class_id, val)

        if expr_node.var:
            return self._resolve_variable_name(expr_node.var.name, env)

        if expr_node.block:
            # Create a Block object and capture the current environment (closure)
            block_info = {
                "node": expr_node.block,
                "captured_env": env,
                "defining_class": defining_class,
            }
            return self._create_obj("Block", block_info)

        if expr_node.send:
            s = expr_node.send
            recv = self.evaluate_expr(s.receiver, env, defining_class)
            # Evaluate arguments in the current environment
            actual_args = [self.evaluate_expr(a.expr, env, defining_class) for a in s.args]

            return self.call_method(recv, s.selector, actual_args, defining_class=defining_class)

        return self._create_obj("Nil")

    def execute_block(self, block_node, args, captured_env: Environment, defining_class=None):
        """Execute a block of code by creating a new scope linked to the captured environment."""
        # Create new environment for the block, inheriting from where the block was defined
        new_env = Environment(parent=captured_env)

        # Fulfill the parameters (Error 51 check implicitly done by XML structure)
        # Naplnění parametrů
        if block_node.parameters:
            for i, p in enumerate(block_node.parameters):
                new_env.values[p.name] = args[i]
                new_env.params.add(p.name)

        # Výchozí hodnota je nil (pokud blok nemá žádné příkazy)
        last_v = self.nil_obj

        for assign in block_node.assigns:
            # Vyhodnotíme pravou stranu
            val = self.evaluate_expr(assign.expr, new_env, defining_class=defining_class)

            # Přiřadíme do cíle (pokud to není zahazovací '_')
            if assign.target.name != "_":
                new_env.assign(assign.target.name, val)

            # Poslední vyhodnocený výraz se stává výsledkem bloku
            last_v = val

        return last_v

    def execute(self, input_io: TextIO) -> None:
        """
        Executes the currently loaded program, using the provided input stream as standard input.
        """
        if not self.current_program:
            return

        # Load classes into the dictionary
        self.classes = {}
        for cls in self.current_program.classes:
            if cls.name in self.classes:
                raise InterpreterError(ErrorCode.SEM_ERROR, f"Class {cls.name} redefined")
            self.classes[cls.name] = cls

        # Arity check in the methods
        for cls in self.classes.values():
            for method in cls.methods:
                expected_params = method.selector.count(":")
                actual_params = len(method.block.parameters or [])
                if expected_params != actual_params:
                    raise InterpreterError(
                        ErrorCode.SEM_ARITY,
                        f"Method {method.selector} in {cls.name} has wrong number of parameters",
                    )

        # 2. Main class existence control
        if "Main" not in self.classes:
            raise InterpreterError(ErrorCode.SEM_MAIN, "Main class missing")

        # 3. "run" method existence check
        # We can use the _find_method
        run_method, _ = self._find_method("Main", "run")
        if not run_method:
            raise InterpreterError(ErrorCode.SEM_MAIN, "Method 'run' missing in Main class")

        # 4. Arity check
        # The "run" method cannot have any parameters
        params_count = len(run_method.block.parameters or [])
        if params_count != 0:
            raise InterpreterError(ErrorCode.SEM_MAIN, "Method 'run' must have 0 parameters")

        # 5. Finally executing
        main_inst = self._create_obj("Main")
        self.call_method(main_inst, "run", [])
