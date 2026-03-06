"""
This module contains the main logic of the interpreter.

IPP: You must definitely modify this file. Bend it to your will.

Author: Ondřej Ondryáš <iondryas@fit.vut.cz>
Author: Radim Pokorný <xpokorr00@stud.fit.vut.cz>
"""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any, Self, TextIO, cast

from lxml import etree
from lxml.etree import ParseError
from pydantic import ValidationError

from .error_codes import ErrorCode
from .exceptions import InterpreterError
from .input_model import Block, Program

logger = logging.getLogger(__name__)


class DummyNode:
    """
    Dummy node for program testing purposes.
    """

    def __init__(self) -> None:
        self.parameters: list[Any] = []
        self.assigns: list[Any] = []


class Environment:
    """
    The main environment of the interpreter.
    """

    def __init__(self, parent: Self | None = None) -> None:
        self.values: dict[str, Any] = {}
        self.parent: Environment | None = parent
        self.params: set[str] = set()  # Error 34 handle (assign to the parameter)

    def lookup(self, name: str) -> Any:
        """Lookup for the variable by name in current and parent scopes"""
        if name == "_":
            raise InterpreterError(ErrorCode.SEM_UNDEF, "Cannot read from '_'")
        if name in self.values:
            return self.values[name]
        if self.parent:
            return self.parent.lookup(name)
        # If no variable is found, throw error 32 (uninitialized/undefined)
        raise InterpreterError(ErrorCode.SEM_UNDEF, f"Variable {name} not defined")

    def assign(self, name: str, value: Any) -> None:
        """Update an existing variable in the scope or create a new one in the current scope"""
        # Check if we are trying to assign to a formal parameter (Error 34)
        curr: Environment | None = self
        while curr:
            if name in curr.values:
                if name in curr.params:
                    raise InterpreterError(
                        ErrorCode.SEM_COLLISION, f"Cannot assign to parameter {name}"
                    )
                curr.values[name] = value
                return
            curr = curr.parent

        if name == "_":  # Ignore the assigment so it won't make any complications
            return

        # If variable does not exist in any parent scope, create it in the current scope
        self.values[name] = value


class Interpreter:
    """
    The main interpreter class, responsible for loading the source file and executing the program.
    """

    def __init__(self) -> None:
        self.current_program: Program | None = None
        self.classes: dict[str, Any] = {}
        # Explicit type annotation for skeletons
        self.nil_obj: dict[str, Any] = {"class": "Nil", "attrs": {}, "val": None}
        self.true_obj: dict[str, Any] = {"class": "True", "attrs": {}, "val": True}
        self.false_obj: dict[str, Any] = {"class": "False", "attrs": {}, "val": False}

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

    def _create_obj(self, class_name: str, value: Any = None) -> dict[str, Any]:
        """Create object method"""
        if class_name == "Nil":
            return self.nil_obj
        if class_name == "True":
            return self.true_obj
        if class_name == "False":
            return self.false_obj
        return {"class": class_name, "attrs": {}, "val": value}

    def _find_method(self, start_class_name: str, selector: str) -> tuple[Any | None, str | None]:
        """Need to find a method by name in the class hierarchy"""
        curr_name: str | None = start_class_name
        while curr_name:
            cls_def = self.classes.get(curr_name)
            if not cls_def:
                break
            # Attempt to find a method in a current class definition
            method = next((m for m in cls_def.methods if m.selector == selector), None)
            if method:
                return method, curr_name
            # Move up the inheritance chain
            curr_name = cls_def.parent
        return None, None

    def _is_subclass(self, child: str, parent: str) -> bool:
        """Check if 'child' class is a subclass of 'parent' class"""
        curr: str | None = child
        while curr:
            if curr == parent:
                return True
            # Get a class definiton to find a possible parent
            cls_def = self.classes.get(curr)
            curr = cls_def.parent if cls_def else None
        return False

    def _handle_static_methods(
        self, r_cls: str, selector: str, args: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Handles messages sent to class objects, such as object creation or static reading.
        """
        # Creates an instance using the value from another object
        if selector == "from:":
            source_obj = args[0]
            source_val = source_obj.get("val")

            # Some built-in types must have an underlying value
            needs_val = (
                r_cls == "Integer"
                or self._is_subclass(str(r_cls), "Integer")
                or r_cls == "String"
                or r_cls == "Block"
            )
            if needs_val and source_val is None:
                raise InterpreterError(
                    ErrorCode.INT_INVALID_ARG,
                    f"Source object lacks internal value for {r_cls}",
                )
            new_obj = self._create_obj(r_cls, source_val)

            # Get a copy of attributes during conversion
            new_obj["attrs"] = source_obj.get("attrs", {}).copy()
            return new_obj

        # Create a new instance of the class
        if selector == "new":
            if r_cls == "Nil":
                return self.nil_obj
            if r_cls == "Block":
                # Blocks require a specific structure for their execution
                dummy_node = DummyNode()
                return self._create_obj(
                    "Block",
                    {
                        "node": dummy_node,
                        "captured_env": Environment(),
                        "defining_class": None,
                    },
                )
            return self._create_obj(r_cls, None)

        # Taking care of an I/O for the string class
        if r_cls == "String" and selector == "read":
            import sys

            line = sys.stdin.readline()
            if not line:
                return self._create_obj("String", "")
            return self._create_obj("String", line.rstrip("\n"))
        raise InterpreterError(
            ErrorCode.SEM_UNDEF, f"Class {r_cls} does not understand {selector}"
        )

    def _handle_universal_methods(
        self, receiver: dict[str, Any], r_cls: str, selector: str, args: list[dict[str, Any]]
    ) -> None | dict[str, Any]:
        """
        Handles identity checks and type-querying methods common to all objects.
        """

        # Check if the two references point to the one same object
        if selector == "identicalTo:":
            res = receiver is args[0]
            return self._create_obj("True" if res else "False", res)

        # Check if the values are equal (Nil, true and false has a special logic)
        if selector == "equalTo:":
            val1 = receiver.get("val")
            val2 = args[0].get("val")
            res = receiver is args[0] if r_cls in ["Nil", "True", "False"] else val1 == val2
            return self._create_obj("True" if res else "False", res)

        # Type check table
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

    def _handle_string_methods(
        self, receiver: dict[str, Any], selector: str, args: list[dict[str, Any]]
    ) -> None | dict[str, Any]:
        """
        Processes methods specific to the String class using a dispatch table.
        """
        # Map selector names to private handler methods
        handlers: dict[str, Callable[[dict[str, Any], list[dict[str, Any]]], dict[str, Any]]] = {
            "print": self._string_print,
            "length": self._string_length,
            "concatenateWith:": self._string_concatenate,
            "startsWith:endsBefore:": self._string_slice,
            "asString": lambda r, a: r,
            "asInteger": self._string_as_int,
        }

        # Find a selector in the dictionary
        if selector in handlers:
            return handlers[selector](receiver, args)

        return None

    def _string_print(
        self, receiver: dict[str, Any], args: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Prints the string with escaped characters handled"""
        val = str(receiver.get("val", ""))

        # Replacing the escape sequences for a normalized standard output
        out = (
            val.replace("\\\\", "\\").replace("\\n", "\n").replace("\\t", "\t").replace("\\'", "'")
        )
        print(out, end="", flush=True)
        return receiver

    def _string_length(
        self, receiver: dict[str, Any], args: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Returns the length of the string after Unicode decoding"""
        s_val = str(receiver.get("val", ""))

        # Decoding the string
        processed_val = s_val.encode("utf-8").decode("unicode_escape")
        return self._create_obj("Integer", len(processed_val))

    def _string_concatenate(
        self, receiver: dict[str, Any], args: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Concatenates two strings if types match"""
        arg_cls = str(args[0].get("class", ""))

        # Check if the object has a type of string or is based on that object
        if arg_cls == "String" or self._is_subclass(arg_cls, "String"):
            return self._create_obj(
                "String", str(receiver.get("val", "")) + str(args[0].get("val", ""))
            )
        return self.nil_obj

    def _string_slice(
        self, receiver: dict[str, Any], args: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Handles the startsWith:endsBefore: slicing logic"""
        s_val = str(receiver.get("val", ""))
        try:
            # Extract the values from Integer objects
            start_idx, end_idx = int(args[0].get("val", 0)), int(args[1].get("val", 0))
            if start_idx <= 0 or end_idx <= 0:
                return self.nil_obj
            if (end_idx - start_idx) <= 0:
                return self._create_obj("String", "")
            return self._create_obj("String", s_val[start_idx - 1 : end_idx - 1])
        except (ValueError, TypeError):
            # Fallback for invalid argument types
            return self.nil_obj

    def _string_as_int(
        self, receiver: dict[str, Any], args: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Converts string value to an integer object"""
        try:
            return self._create_obj("Integer", int(receiver.get("val", 0)))
        except (ValueError, TypeError):
            return self.nil_obj

    def _handle_integer_methods(
        self, receiver: dict[str, Any], selector: str, args: list[dict[str, Any]]
    ) -> None | dict[str, Any]:
        """
        Processes methods specific to the Integer class and its subclasses using a dispatch table.
        """
        handlers: dict[
            str, Callable[[dict[str, Any], str, list[dict[str, Any]]], dict[str, Any]]
        ] = {
            "divBy:": self._int_div,
            "asString": self._int_as_string,
            "asInteger": lambda r, s, a: r,
            "plus:": self._int_arithmetic,
            "minus:": self._int_arithmetic,
            "multiplyBy:": self._int_arithmetic,
            "greaterThan:": self._int_arithmetic,
            "timesRepeat:": self._int_times_repeat,
        }

        # Find a selector in the dictionary
        if selector in handlers:
            return handlers[selector](receiver, selector, args)
        return None

    def _int_div(
        self, receiver: dict[str, Any], selector: str, args: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Handles integer division with zero-check"""
        argval2 = args[0].get("val", 0)
        if argval2 == 0:
            raise InterpreterError(ErrorCode.INT_INVALID_ARG, "Division by zero")
        return self._create_obj("Integer", receiver.get("val", 0) // argval2)

    def _int_as_string(
        self, receiver: dict[str, Any], selector: str, args: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Converts integer value to a string object"""
        return self._create_obj("String", str(receiver.get("val", 0)))

    def _int_arithmetic(
        self, receiver: dict[str, Any], selector: str, args: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Handles basic arithmetic and comparison for integers"""
        arg = args[0]

        arg_cls = str(arg.get("class", ""))

        # Integer check
        if not (arg_cls == "Integer" or self._is_subclass(arg_cls, "Integer")):
            raise InterpreterError(
                ErrorCode.INT_OTHER, f"Operand for {selector} must be an Integer"
            )

        val1, val2 = receiver.get("val", 0), arg.get("val", 0)

        # Switch case for the operators
        if selector == "plus:":
            return self._create_obj("Integer", val1 + val2)
        if selector == "minus:":
            return self._create_obj("Integer", val1 - val2)
        if selector == "multiplyBy:":
            return self._create_obj("Integer", val1 * val2)
        if selector == "greaterThan:":
            return self._create_obj("True" if val1 > val2 else "False", val1 > val2)
        # If no valid operator was found, throw an error
        raise InterpreterError(ErrorCode.INT_OTHER, f"Unsupported arithmetic selector {selector}")

    def _int_times_repeat(
        self, receiver: dict[str, Any], selector: str, args: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Executes a block N times, where N is the receiver's value"""
        n = int(receiver.get("val", 0))
        last_res = self.nil_obj
        block = args[0]
        # Does block have a parameters?
        has_p = len(block.get("val", {}).get("node").parameters or []) > 0

        for i in range(1, n + 1):
            idx_obj = self._create_obj("Integer", i)
            if has_p:
                last_res = self.call_method(block, "value:", [idx_obj])
            else:
                last_res = self.call_method(block, "value", [])
        return last_res

    def _handle_block_methods(
        self, receiver: dict[str, Any], selector: str, args: list[dict[str, Any]]
    ) -> None | dict[str, Any]:
        """
        Processes methods specific to the Block class, including execution and loops.
        """
        if selector.startswith("value"):
            data = receiver["val"]
            if not data or "node" not in data:
                return self.nil_obj
            # Check the arity
            if len(args) != len(data["node"].parameters or []):
                raise InterpreterError(ErrorCode.SEM_ARITY, "Wrong number of arguments for block")
            # Execute the block in the specific environment
            return self.execute_block(
                data["node"], args, data["captured_env"], defining_class=data.get("defining_class")
            )
        # Loop case continues as long as the receiver block returns True
        if selector == "whileTrue:":
            body, last_res = args[0], self.nil_obj
            # Evaluate the condition each time
            while self.call_method(receiver, "value", []) is self.true_obj:
                last_res = self.call_method(body, "value", [])
            return last_res
        return None

    def _handle_boolean_nil_methods(
        self, r_cls: str, selector: str, args: list[dict[str, Any]]
    ) -> None | dict[str, Any]:
        """
        Processes methods specific to Boolean (True/False) and Nil classes.
        """
        if r_cls in ["True", "False"]:
            # Logical inversion
            if selector == "not":
                return self.false_obj if r_cls == "True" else self.true_obj
            if selector == "and:":
                return (
                    self.false_obj if r_cls == "False" else self.call_method(args[0], "value", [])
                )
            # Execute block only if the receiver state matches
            if selector == "ifTrue:":
                return self.call_method(args[0], "value", []) if r_cls == "True" else self.nil_obj
            if selector == "ifFalse:":
                return self.call_method(args[0], "value", []) if r_cls == "False" else self.nil_obj
            if selector == "or:":
                return self.true_obj if r_cls == "True" else self.call_method(args[0], "value", [])
            if selector == "ifTrue:ifFalse:":
                return self.call_method(args[0] if r_cls == "True" else args[1], "value", [])
            if selector == "asString":
                return self._create_obj("String", r_cls.lower())
        # Nil special behavior
        if r_cls == "Nil" and selector == "asString":
            return self._create_obj("String", "nil")
        return None

    def _handle_builtin_specializations(
        self, receiver: dict[str, Any], r_cls: str, selector: str, args: list[dict[str, Any]]
    ) -> None | dict[str, Any]:
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

    def _handle_attribute_access(
        self,
        receiver: dict[str, Any],
        selector: str,
        args: list[dict[str, Any]],
        start_lookup: str,
    ) -> None | dict[str, Any]:
        """
        Handles dynamic attribute access including getters and setters with collision checks.
        """

        # If the selector ends with ':', it's a potential assignment
        if selector.endswith(":"):
            attr_name = selector[:-1]

            # Does the name exist in the class hierarchy?
            collision, _ = self._find_method(start_lookup, attr_name)
            if collision:
                raise InterpreterError(
                    ErrorCode.INT_INST_ATTR, f"Error 54: Collision with method {attr_name}"
                )

            # Create it if it does not exist
            receiver.setdefault("attrs", {})[attr_name] = args[0]
            return receiver

        # If the selector matches a key in the object
        if selector in receiver.get("attrs", {}):
            val = receiver["attrs"][selector]
            if isinstance(val, dict):
                return val
            return None

        # Fallback for generic objects
        if selector == "asString":
            return self._create_obj("String", "")
        return None

    def call_method(
        self,
        receiver: Any,
        selector: str,
        args: list[dict[str, Any]],
        defining_class: str | None = None,
        use_super: bool = False,
    ) -> dict[str, Any]:
        """Global function to handle the methods in the program"""
        if isinstance(receiver, dict) and receiver.get("_is_super_wrapper"):
            use_super = True
            receiver = receiver["_inner_obj"]

        r_cls = receiver.get("class")
        if r_cls == "Block" and defining_class is None:
            defining_class = receiver.get("val", {}).get("defining_class")

        # Class-level messages
        if receiver.get("is_class"):
            return self._handle_static_methods(r_cls, selector, args)

        # Universal Object methods
        res = self._handle_universal_methods(receiver, r_cls, selector, args)
        if res is not None:
            return res

        # Built-in Class Specializations
        res = self._handle_builtin_specializations(receiver, r_cls, selector, args)
        if res is not None:
            return res

        # User-defined Method Lookup
        start_lookup = r_cls
        if use_super:
            ctx_class = self.classes.get(str(defining_class))
            if ctx_class and ctx_class.parent:
                start_lookup = ctx_class.parent
            else:
                raise InterpreterError(ErrorCode.INT_DNU, f"Super method {selector} not found")

        # Find a method in the environment
        method, method_class = self._find_method(start_lookup, selector)
        if method:
            method_env = Environment()
            method_env.values["self"] = receiver
            return self.execute_block(method.block, args, method_env, defining_class=method_class)

        # Attribute access (Getters/Setters)
        res = self._handle_attribute_access(receiver, selector, args, start_lookup)
        if res is not None:
            return res

        # If everything fails
        raise InterpreterError(ErrorCode.INT_DNU, f"Method {selector} not found for class {r_cls}")

    def _resolve_variable_name(self, name: str, env: Environment) -> dict[str, Any]:
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

        # Let's find the name in all dicts
        if name in constants:
            return constants[name]

        if name == "self":
            return cast(dict[str, Any], env.lookup("self"))

        if name == "super":
            obj = env.lookup("self")
            return {"_is_super_wrapper": True, "_inner_obj": obj}

        # Check if we know the object name
        builtin_classes = {"Integer", "String", "Object", "Nil", "True", "False", "Block"}
        if name in self.classes or name in builtin_classes:
            return {"class": name, "is_class": True, "val": name}

        # We need to lookup
        return cast(dict[str, Any], env.lookup(name))

    def evaluate_expr(
        self, expr_node: Any, env: Environment, defining_class: str | None = None
    ) -> dict[str, Any]:
        """Evaluate an expression node and return its value within the given environment"""

        # If the value is literal, let's find in the classes or create a new object
        if expr_node.literal:
            lit = expr_node.literal
            if lit.class_id == "class":
                return {"class": lit.value, "is_class": True, "val": lit.value}
            val = int(lit.value) if lit.class_id == "Integer" else lit.value
            return self._create_obj(lit.class_id, val)

        # Find the variable name in the nodes
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

        # If we have a sender flag evaluate the expression
        if expr_node.send:
            s = expr_node.send
            recv = self.evaluate_expr(s.receiver, env, defining_class)
            # Evaluate arguments in the current environment
            actual_args = [self.evaluate_expr(a.expr, env, defining_class) for a in s.args]

            return self.call_method(recv, s.selector, actual_args, defining_class=defining_class)

        return self._create_obj("Nil")

    def execute_block(
        self,
        block_node: Block,
        args: list[dict[str, Any]],
        captured_env: Environment,
        defining_class: str | None = None,
    ) -> dict[str, Any]:
        """Execute a block of code by creating a new scope linked to the captured environment"""
        # Create new environment for the block, inheriting from where the block was defined
        new_env = Environment(parent=captured_env)

        # Fulfill the parameters (Error 51 check implicitly done by XML structure)
        if block_node.parameters:
            for i, p in enumerate(block_node.parameters):
                new_env.values[p.name] = args[i]
                new_env.params.add(p.name)

        # value is nil if there are no commands in the block
        last_v = self.nil_obj

        for assign in block_node.assigns:
            # Evaluate the right side of the expression
            val = self.evaluate_expr(assign.expr, new_env, defining_class=defining_class)

            # assign to the target
            if assign.target.name != "_":
                new_env.assign(assign.target.name, val)

            # Last expression is the result
            last_v = val

        return last_v

    def _prepare_classes(self) -> None:
        """
        Loads classes and prevents redefinition of built-in types
        """
        self.classes = {}
        builtin_names = {"Integer", "String", "Object", "Nil", "True", "False", "Block"}

        if not self.current_program:
            return

        # Class redefining checks
        for cls in self.current_program.classes:
            if cls.name in builtin_names:
                raise InterpreterError(
                    ErrorCode.SEM_ERROR, f"Cannot redefine builtin class {cls.name}"
                )
            if cls.name in self.classes:
                raise InterpreterError(
                    ErrorCode.SEM_ERROR, f"Class {cls.name} redefined: {cls.name}"
                )
            self.classes[cls.name] = cls

    def _validate_program_structure(self) -> None:
        """
        Performs static checks
        """
        # Method arity check
        for cls in self.classes.values():
            for method in cls.methods:
                expected = method.selector.count(":")
                actual = len(method.block.parameters or [])
                if expected != actual:
                    raise InterpreterError(
                        ErrorCode.SEM_ARITY, f"Arity mismatch in {cls.name}>>{method.selector}"
                    )

        # Main class and run method existence check
        if "Main" not in self.classes:
            raise InterpreterError(ErrorCode.SEM_MAIN, "Main class missing")

        run_method, _ = self._find_method("Main", "run")
        if not run_method:
            raise InterpreterError(ErrorCode.SEM_MAIN, "Method 'run' missing in Main class")

        # 'run' method arity check
        if len(run_method.block.parameters or []) != 0:
            raise InterpreterError(ErrorCode.SEM_MAIN, "Method 'run' must have 0 parameters")

    def execute(self, input_io: TextIO) -> None:
        """
        Executes the currently loaded program.
        """
        if not self.current_program:
            return

        # Prepare and validate (splits complexity)
        self._prepare_classes()
        self._validate_program_structure()

        # Start execution by sending 'run' to a new Main instance
        main_inst = self._create_obj("Main")
        self.call_method(main_inst, "run", [])
