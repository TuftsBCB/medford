# src/MEDFORD/objs/outwriter.py

from typing import Dict, Optional, Any, List


class OutWriter:
    """
    Writes parsed blocks back out for fidelity testing (--out).
    Keeps formatting/ordering stable and preserves comments.
    """

    def __init__(self, line_collector: Any):
        # Only used to access .comments (if present)
        self.line_collector = line_collector

    def render_block(self, block: Any, resolved_macros: Optional[Dict[str, str]] = None) -> str:
        """
        Outputs a block as MEDFORD text:

        @<MAJOR> <header_value>
        @<MAJOR>-<minor> <content>
        """
        # Major tag name
        if getattr(block, "major_tokens", None):
            major = "_".join(block.major_tokens)
        else:
            major = "Block"

        lines: List[str] = []

        # Header detail (first detail)
        header_value = ""
        if getattr(block, "details", None) and block.details:
            if resolved_macros is None:
                header_value = block.details[0].get_raw_content().strip()
            else:
                header_value = block.details[0].get_content(resolved_macros).strip()

        lines.append(f"@{major} {header_value}")

        # Minor details
        if getattr(block, "details", None):
            for d in block.details[1:]:
                if getattr(d, "minor_token", None):
                    if resolved_macros is None:
                        content = d.get_raw_content().strip()
                    else:
                        content = d.get_content(resolved_macros).strip()
                    lines.append(f"@{major}-{d.minor_token} {content}")

        return "\n".join(lines)

    def write_blocks(
        self,
        blocks: List[Any],
        path: str,
        resolved_macros: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Writes blocks to `path`, inserting comments in approximate original positions.

        Strategy:
        - Sort comments by line number (best effort)
        - For each block, write any comments with lineno <= block start lineno
        - Then write block
        - Finally write trailing comments
        """
        comments = list(getattr(self.line_collector, "comments", []) or [])

        def _cln(x: Any) -> int:
            return self._obj_lineno(x, -1)

        comments.sort(key=_cln)

        idx = 0
        with open(path, "w", encoding="utf-8") as f:
            wrote_any = False
            prev_blank = False

            def sep():
                nonlocal prev_blank, wrote_any
                if wrote_any and not prev_blank:
                    f.write("\n")
                    prev_blank = True

            def write_line(s: str):
                nonlocal prev_blank, wrote_any
                s = s.rstrip("\n")
                f.write(s + "\n")
                wrote_any = True
                prev_blank = (s.strip() == "")

            def write_block_text(text: str):
                for line in text.splitlines():
                    write_line(line)

            for b in blocks:
                b_start = self._block_start_lineno(b)

                # Comments that occur before or on this block's first line
                while idx < len(comments) and _cln(comments[idx]) <= b_start:
                    sep()
                    write_line(self._comment_text(comments[idx]))
                    idx += 1

                # Write the block itself
                sep()
                write_block_text(self.render_block(b, resolved_macros))

            # Trailing comments after last block
            while idx < len(comments):
                sep()
                write_line(self._comment_text(comments[idx]))
                idx += 1

    def _comment_text(self, c: Any) -> str:
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

    def _obj_lineno(self, obj: Any, default_if_missing: int) -> int:
        for name in ("line_number", "lineno", "lineNo", "line_index", "idx"):
            v = getattr(obj, name, None)
            if isinstance(v, int):
                return v

        for holder in ("line", "source", "src", "origin"):
            sub = getattr(obj, holder, None)
            if sub is None:
                continue
            for name in ("line_number", "lineno", "lineNo", "line_index", "idx"):
                v = getattr(sub, name, None)
                if isinstance(v, int):
                    return v

        return default_if_missing

    def _block_start_lineno(self, b: Any) -> int:
        # Prefer Detail.get_linenos()[0] if available
        if getattr(b, "details", None) and b.details:
            d0 = b.details[0]

            # 1) Best: Detail.get_linenos()
            if hasattr(d0, "get_linenos") and callable(d0.get_linenos):
                try:
                    lns = d0.get_linenos()
                    if isinstance(lns, (list, tuple)) and lns:
                        ln0 = lns[0]
                        if isinstance(ln0, int):
                            return ln0
                except Exception:
                    pass

            # 2) Fallback: check headline object
            h = getattr(d0, "headline", None)
            if h is not None:
                ln = self._obj_lineno(h, None)
                if isinstance(ln, int):
                    return ln

        return self._obj_lineno(b, 10**9)
