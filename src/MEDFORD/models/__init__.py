from typing import Dict, List
from . import generics

__all__ = ["generics"]

def models_get_major_minors() -> Dict[str, List[str]] :
    out: dict[str, List[str]] = {}
    out.update(generics.DefinedMajorMinor)
    return out
