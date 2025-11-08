"""Module containing the MEDFORD parser, which can validate and compile MEDFORD
metadata files."""

import sys
import os
from typing import List, Dict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from enum import Enum
from pathlib import PurePath  # ?

from .objs.linereader import LineReader, Line
from .objs.linecollector import LineCollector, Macro, Block
from .objs.dictionizer import Dictionizer
from .models.generics import Entity
from .objs.linecollections import Detail
from .objs.bagitHandler import BagItHandler
from .objs.medfordValidator import Validator

import argparse
import json
from .objs.linecollections import Detail
from .objs.bagitHandler import BagItHandler

import sys
import os
from typing import List, Dict
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) #TODO terminal would not recognize bagithandler without this

import argparse
import json
from . import mfdglobals
from .models import models_get_major_minors

from . import mfdglobals



# order of ops:
# 1. open file
# 2. turn all lines into Line objs (using LineReader)
# 3. turn Line objs into specialized objs (using LineCollector)
# 4. turn specialized objs into dict (using ?)
# 5. verify dict using Pydantic (using ?)



# TODO : add error mgmt
class ParserMode(Enum):
    """Enum storing the mode of operation of the MEDFORD parser."""

    VALIDATE = "validate"
    COMPILE = "compile"

    def __str__(self):
        return self.value
    

def process_blocks_to_dict(blocks):
    combined_dict = {}

    for block in blocks:
        if not hasattr(block, "major_tokens") or not block.major_tokens:
            continue

        major_token = block.major_tokens[0]
        # hard code joining token with underscore
        if len(block.major_tokens) > 0:
            major_token = "_".join(block.major_tokens)

        # Initialize category if needed
        if major_token not in combined_dict:
            combined_dict[major_token] = []

        block_dict = {}
        if hasattr(block, "details") and block.details:
            # get header (first value)
            header_detail = block.details[0]
            block_dict["value"] = header_detail.get_raw_content().strip()

            # process minor tokens
            for detail in block.details[1:]:
                if detail.minor_token:
                    minor_token = detail.minor_token
                    content = detail.get_raw_content().strip()

                    if minor_token not in block_dict:
                        block_dict[minor_token] = []

                    block_dict[minor_token].append(content)

        # add processed block to its major category
        combined_dict[major_token].append(block_dict)

    return combined_dict

def validate_blocks(blocks, validator, filename):
    for block in blocks:
        if not hasattr(block, "major_tokens") or not block.major_tokens:
            continue

        major_token = block.major_tokens[0]
        # hard code joining token with underscore
        if len(block.major_tokens) > 0:
            major_token = "_".join(block.major_tokens)

        if hasattr(block, "details") and block.details:
            header_detail = block.details[0]
            header_value = header_detail.get_raw_content().strip()
            line_number = getattr(header_detail, 'line_number', None) or getattr(block, 'line_number', None)
            
            validator.validate(major_token, header_value, line_number, filename)

            for detail in block.details[1:]:
                if detail.minor_token:
                    minor_token = detail.minor_token
                    content = detail.get_raw_content().strip()
                    
                    full_tag = f"{major_token}-{minor_token}"
                    line_number = getattr(detail, 'line_number', None)
                    
                    validator.validate(full_tag, content, line_number, filename)



class OutputMode(Enum):
    """Enum storing possible outout types of the MEDFORD parser."""

    OTHER = "OTHER"
    BCODMO = "BCODMO"
    RDF = "RDF"
    BAGIT = "BAGIT"
    # TODO : Make creating a bag a separate option?
    # Could want to make an output RDF file AND zip it.

    def __str__(self):
        return self.value

    @classmethod
    def _missing_(cls, value: str):
        for member in cls:
            if member.name.lower() == value.lower():
                return member
        return None
    

class MFD:
    """Base class runner of the MEDFORD parser.
    Runs entire validation/compilation pipeline from file input to output."""

    # TODO : ? is this the right way to implement this?
    @classmethod
    def get_version(cls) -> str:
        return mfdglobals.version

    mfdglobals.init()

    filename: str
    object_lines: List[Line]
    line_collector: LineCollector
    dictionizer: Dictionizer

    write_json: bool
    output_path: str

    macro_definitions: Dict[str, Macro]
    blocks: List[Block]
    named_blocks: Dict[str, Block]

    dict_data = None
    pydantic_version = None

    def __init__(
        self,
        filename,
        mode: OutputMode = OutputMode.OTHER,
        action: ParserMode = None,
        base_dir: str = None,
        write_json: bool = True,
        output_path: str = ".",
    ):
        self.filename = filename
        self.mode = mode
        self.action = action  # Store the action
        self.base_dir = base_dir
        self.write_json = write_json
        self.output_path = output_path
        self.validatorFile = "medford.mvd"

        try:
            self.validator = Validator("medford.mvd")  # No ValidationData needed for now
        except FileNotFoundError:
            print("Warning: medford.mvd validation file not found. Skipping validation.")
            self.validator = None

    # --- DEV helper: write the parsed blocks back out for fidelity testing
    def _render_block(self, block, resolved_macros: Dict[str, str] | None = None) -> str:
        """
        Function that outputs parsed blocks for testing:
        @<MAJOR> <header_value>
        @<MAJOR>-<minor> <content>
        """        

        # get Major tag name
        if getattr(block, "major_tokens", None):
            major = "_".join(block.major_tokens)
        else:
            major = "Block"

        lines = []

        # get major tag header (first detail)
        header_value = ""
        if getattr(block, "details", None) and block.details:
            if resolved_macros is None:
                header_value = block.details[0].get_raw_content().strip()
            else:
                header_value = block.details[0].get_content(resolved_macros).strip()
        lines.append(f"@{major} {header_value}")

        # add subsequent details of the  minor tags
        if getattr(block, "details", None):
            for d in block.details[1:]:
                if getattr(d, "minor_token", None):
                    if resolved_macros is None:
                        content = d.get_raw_content().strip()
                    else:
                        content = d.get_content(resolved_macros).strip()
                    lines.append(f"@{major}-{d.minor_token} {content}")
        return "\n".join(lines)
    
    def _write_blocks(self, blocks, path: str, resolved_macros: Dict[str, str] | None = None) -> None:
        """
        Function that writes out parsed blocks:
        """    
        comments = list(getattr(self.line_collector, "comments", []) or [])

        # Returns the line number for a comment object.
        def _cln(x):  
            return self._obj_lineno(x, -1)

        # Sort comments by line number
        comments.sort(key=_cln)

        idx = 0
        with open(path, "w", encoding="utf-8") as f:
            wrote_any = False
            prev_blank = False

            # Inserts a blank line in the output only if the previous line was not blank 
            # helps visually separate blocks/comments.
            def sep():
                nonlocal prev_blank, wrote_any
                if wrote_any and not prev_blank:
                    f.write("\n")
                    prev_blank = True

            # Writes a single line to the file; updates flags to track if the last line was blank
            def write_line(s: str):
                nonlocal prev_blank, wrote_any
                s = s.rstrip("\n")
                f.write(s + "\n")
                wrote_any = True
                prev_blank = (s.strip() == "")

            # Writes each line from block's multi-line text using write_line
            def write_block_text(text: str):
                for line in text.splitlines():
                    write_line(line)

            for b in blocks:
                b_start = self._block_start_lineno(b)

                # comments that occur before or on this block's first line
                while idx < len(comments) and _cln(comments[idx]) <= b_start:
                    sep()
                    write_line(self._comment_text(comments[idx]))
                    idx += 1

                # write the block itself
                sep()
                write_block_text(self._render_block(b, resolved_macros))

            # write the trailing comments after the last block in the file
            while idx < len(comments):
                sep()
                write_line(self._comment_text(comments[idx]))
                idx += 1


    def _comment_text(self, c) -> str:
        # Try common fields in a safe order
        if hasattr(c, "get_raw_content") and callable(c.get_raw_content):
            raw = c.get_raw_content()
        elif hasattr(c, "raw"):
            raw = c.raw
        elif hasattr(c, "content"):
            raw = c.content
        elif hasattr(c, "text"):
            raw = c.text
        elif hasattr(c, "line"):
            raw = c.line
        else:
            raw = str(c)

        raw = str(raw).rstrip("\n")
        s = raw.lstrip()

        # Ensure it prints as a proper comment line
        if s.startswith("#"):
            return s
        return "# " + s
    
    def _obj_lineno(self, obj, default_if_missing: int) -> int:
        # Keep the generic fallback
        for name in ("line_number", "lineno", "lineNo", "line_index", "idx"):
            v = getattr(obj, name, None)
            if isinstance(v, int):
                return v
        # Try common nested holders
        for holder in ("line", "source", "src", "origin"):
            sub = getattr(obj, holder, None)
            if sub is None:
                continue
            for name in ("line_number", "lineno", "lineNo", "line_index", "idx"):
                v = getattr(sub, name, None)
                if isinstance(v, int):
                    return v
        return default_if_missing

    def _block_start_lineno(self, b):
        # Prefer Detail.get_linenos()[0] if available
        if getattr(b, "details", None) and b.details:
            d0 = b.details[0]
            # 1) best: Detail.get_linenos()
            if hasattr(d0, "get_linenos") and callable(d0.get_linenos):
                try:
                    lns = d0.get_linenos()
                    if isinstance(lns, (list, tuple)) and lns:
                        ln0 = lns[0]
                        if isinstance(ln0, int):
                            return ln0
                except Exception:
                    pass
            # 2) fallback: look into the headline object
            h = getattr(d0, "headline", None)
            if h is not None:
                ln = self._obj_lineno(h, None)
                if isinstance(ln, int):
                    return ln
        return self._obj_lineno(b, 10**9)




    def run_medford(self):
        """Main function that runs MEDFORD compilation from start to finish."""
        self.em_inst = mfdglobals.validator  # this is just for debug purposes

        # TODO: way to avoid putting all lines into memory?
        # TODO: make LineProcessor take all of the strs/filename and do
        #       the work itself?
        # 1, 2
        self.object_lines = MFD._get_line_objects(self.filename)

        # 3
        self.line_collector = MFD._get_line_collector(self.object_lines)
        self.macro_definitions = self.line_collector.get_macros()
        self.blocks = self.line_collector.get_flat_blocks()
        self.named_blocks = self.line_collector.get_1lvl_blocks()

        # check to see if macros are already expanded before we write
        print("[dev] macros collected:", len(getattr(self, "macro_definitions", {}) or {}))
        if self.blocks and self.blocks[0].details:
            d0 = self.blocks[0].details[0]
            print("[dev] detail0.has_macros:", getattr(d0, "has_macros", None))
            print("[dev] detail0.used_macro_names:", getattr(d0, "used_macro_names", None))


        # stop here and check for syntax errors
        if mfdglobals.mv.instance().has_syntax_err():
            print("Syntax errors found! : ")
            print(f"{mfdglobals.mv.instance().n_syntax_errs()} errors")
            mfdglobals.mv.instance().print_syntax_errs()
            sys.exit(1)
            # TODO : enter error mode

        # 4
        self.dictionizer = MFD._get_dictionizer(
            self.macro_definitions, self.named_blocks
        )
        self.dict_data = self.dictionizer.generate_dict(self.blocks)

        if mfdglobals.mv.instance().has_other_err():
            print("Other errors found! : ")
            print(f"{mfdglobals.mv.instance().n_other_errs()} errors")
          
        # 5
        # TODO : this kind of breaks all of my type checking and requires
        # me to use Dict[str, Any] instead of Dict[str, Dict[...]]...
        # maybe in the future look into fixing this?
        #   The problem is that Blocks aren't Dicts.
        # self.pydantic_version = Entity(**self.dict_data)
        try:
            self.pydantic_version = Entity(**self.dict_data)
            if mfdglobals.debug:
                print("Entity created successfully")
        except Exception as e:
            print(f"Entity creation failed: {e}")
            import traceback
            traceback.print_exc()
            
        if mfdglobals.mv.instance().has_pydantic_err():
            sys.stderr.write("has error\n")
            mfdglobals.mv.instance().print_pydantic_errs()
            sys.exit(1)
        
        if self.validator:
            print("Running MEDFORD validation...")
            validate_blocks(self.blocks, self.validator, self.validatorFile)
            validation_passed = self.validator.print_validation_summary()
            if not validation_passed:
                print("Validation failed.")


        
        #try:
        #    self.pydantic_version = Entity(**self.dict_data)
        #    print(self.pydantic_version.dict())
        # except ValidationError as e:
        #    if(len(e.errors()) != mfdglobals.mv.instance().n_pydantic_errs()) :
        #        print("ERROR: Validation errors are not all being accounted for by the validator.")
        #        raise Exception("Missing validation errors")
        #    else :
        #        if mfdglobals.mv.instance().has_pydantic_err() :
        #            mfdglobals.mv.instance().print_pydantic_errs()

        # TODO: export to json, bag
        # TODO: implement all of the old models
        #print("No errors found in the provided MEDFORD file!")


        # If user specified --out, dump blocks now (after dictionrizer and validation)
        if getattr(self, "dev_out_path", None):
            try:
                self._write_blocks(self.blocks, self.dev_out_path, resolved_macros=self.dictionizer.resolved_macros)
                print(f"[dev] Wrote blocks to: {self.dev_out_path}")
            except Exception as e:
                print(f"[dev] Failed to write --out file: {e}")
        

        if self.write_json:
            if self.output_path == ".":
                with open("medford_output.json", "w", encoding="utf-8") as f:
                    combined_data = process_blocks_to_dict(self.blocks)
                    json.dump(combined_data, f, indent=2)
            else :
                raise NotImplementedError("Output paths other than '.' not yet supported.")
                #     json.dump(self.dict_data, f, indent=2)
# TODO: export to json, bag
        # TODO: implement all of the old models
        if self.mode == OutputMode.BAGIT:
            # Process blocks to dictionary format
            combined_data = process_blocks_to_dict(self.blocks)

            bagit_handler = BagItHandler(
                combined_data, self.base_dir, self.output_path, self.filename
            )

            # Note: This should be self.action, not self.ParserMode
            if self.action == ParserMode.VALIDATE:
                if bagit_handler._validate():
                    print("BagIt validation passed.")
                else:
                    print("BagIt validation failed.")
                    sys.exit(1)

            # Note: This should be self.action, not self.ParserMode
            elif self.action == ParserMode.COMPILE:
                pass
                # Compile BagIt package
                try:
                    bag_path = bagit_handler._compile()
                    print(f"BagIt package created at: {bag_path}")
                except Exception as e:
                    print(f"Error creating BagIt package: {e}")
                    sys.exit(1)
    @classmethod
    def _get_line_objects(cls, filename: str) -> List[Line]:
        object_lines = []
        with open(filename, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f.readlines()):
                p_line = LineReader.process_line(line, idx)
                if p_line is not None:
                    object_lines.append(p_line)

        return object_lines


    # for testing purposes in model unit tests
    @classmethod
    def _get_unvalidated_blocks(cls, input: str) -> List[Block]:
        object_lines = MFD._get_line_objects(input)
        line_collector = MFD._get_line_collector(object_lines)
        # macro_definitions = line_collector.get_macros()

        blocks = line_collector.get_flat_blocks()

        return blocks

    # note for later: what happens when it takes too long to process ?
    # user writes a new line, add it to LineCollector that single line at a
    # time?
    # 10s of ms amount of time to run is allocation usually
    @classmethod
    def _get_line_collector(cls, object_lines: List[Line]) -> LineCollector:
        return LineCollector(object_lines)

    @classmethod
    def _get_dictionizer(
        cls, macro_definitions: Dict[str, Macro], name_dictionary: Dict[str, Block]
    ) -> Dictionizer:
        return Dictionizer(macro_definitions, name_dictionary)


ap = argparse.ArgumentParser(prog="medford")
# basic arguments
ap.add_argument(
    "action",
    type=ParserMode,
    choices=list(ParserMode),
    help="Whether to run the MEDFORD parser in Validation or "
    "Compilation mode. (Compilation creates a novel output file.)",
)
ap.add_argument("file", type=str, help="Input MEDFORD file to validate or compile.")
ap.add_argument(
    "-m",
    "--mode",
    type=OutputMode,
    choices=list(OutputMode),
    default=OutputMode.OTHER,
    help="The output mode of the MEDFORD parser; what format "
    "should be validated against or compiled to.",
)

# argument for base directory of files for BagIT
ap.add_argument(
    "--dir",
    type=str,
    help="Base directory of files described in the given Medford "
    "file for BagIt compression.",
)
# argument for "permissible" mode
ap.add_argument(
    "--permissible",
    action="store_true",
    default=False,
    help="Enables permissible mode for the MEDFORD parser. "
    "This disables a significant number of the parser's validation "
    "features. (not implemented)",
)

# debug arguments

ap.add_argument(
    "--write_json",
    action="store_true",
    default=False,
    help="FOR DEBUG: Write a JSON file of the internal "
    "representation of the MEDFORD file beside the input MEDFORD "
    "file.",
)
ap.add_argument(
    "--out",
    metavar="filename.mfd",
    help="(DEV) write parsed blocks back out as MEDFORD text for fidelity testing."
)
ap.add_argument(
    "-d",
    "--debug",
    action="store_true",
    default=False,
    help="FOR DEBUG: Enable DEBUG mode for MEDFORD, enabling a "
    "significant amount of intermediate stdout output. "
    "(currently unimplemented.)",
)
ap.add_argument(
    "-v",
    "--version",
    action="version",
    version="%(prog)s {version}".format(version=MFD.get_version()),
)

# wants to: ask parser what major/minor tokens it understands
# -> dumping schema of Entity & parsing manually

# syntax check -> get back both line objects & errors

# want full API call to include all minor api calls;
# return dict w/ string indices?


def provide_args_and_go(
    action: ParserMode,
    file: str,
    mode: OutputMode,
    base_dir: str = ".",
    write_json: bool = False,  # changed base_dir default from None to "."
    output_path: str = ".",
    debug: bool = False,
):
    mfdglobals.debug = debug
    mfd = MFD(file, mode, action, base_dir, write_json, output_path)
    mfd.run_medford()


def parse_args_and_go():
    #print("running")
    args = ap.parse_args()
    mfdglobals.debug = args.debug
    mfd = MFD(
        args.file,
        mode=args.mode,
        action=args.action,
        base_dir=args.dir,
        write_json=args.write_json,
        output_path=".",
    )
    mfd.dev_out_path = args.out  #makes --out value available to run_medford()
    mfd.run_medford()


#def provide_args_and_go(action:ParserMode, file:str, mode:OutputMode, debug:bool = False, write_json:bool = False) :
#    mfdglobals.debug = debug
#    mfd = MFD(PurePath(file), write_json=write_json)
#    mfd.run_medford()

def get_major_minors() -> Dict[str, List[str]] :
    return models_get_major_minors()

if __name__ == "__main__" :
    parse_args_and_go()
