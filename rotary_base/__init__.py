"""Authoritative rotary-base geometry and parameters for the arm and test fixture."""
import json,pathlib
from .core import build,print_shape,spindle_fit_checks
def parameters():return json.loads((pathlib.Path(__file__).parent/"parameters.json").read_text())
