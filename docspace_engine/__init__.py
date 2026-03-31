from pathlib import Path

_pkg_dir = Path(__file__).resolve().parent
_src_pkg_dir = _pkg_dir.parent / "src" / "docspace_engine"
__path__ = [str(_src_pkg_dir)]
