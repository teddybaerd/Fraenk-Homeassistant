"""Tests for fraenk API request compatibility."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types

ROOT = Path(__file__).parents[1]
PACKAGE = ROOT / "custom_components" / "fraenk_mobile"

# Import api.py without importing Home Assistant-dependent package __init__.py.
package = types.ModuleType("fraenk_mobile")
package.__path__ = [str(PACKAGE)]
sys.modules["fraenk_mobile"] = package
for module_name in ("const", "api"):
    spec = importlib.util.spec_from_file_location(
        f"fraenk_mobile.{module_name}", PACKAGE / f"{module_name}.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

from fraenk_mobile.api import build_correlation_id, build_form  # noqa: E402


def test_okhttp_form_encoding() -> None:
    """The form body must match OkHttp FormBody encoding and order."""
    assert build_form(
        [
            ("scope", "app permanent"),
            ("username", "markus+test@example.de"),
            ("password", "a b+c~d"),
        ]
    ) == (
        "scope=app+permanent&username=markus%2Btest%40example.de"
        "&password=a+b%2Bc%7Ed"
    )


def test_correlation_id() -> None:
    """The correlation hash must match the Android implementation."""
    body = (
        "grant_type=password&username=test%40example.com&"
        "password=P%40ss+word&scope=app+permanent"
    )
    assert build_correlation_id(body) == (
        "264b50908500f727c40310ca91fd79b2f"
        "0cd8f8766f1cb4b99e9f60198760331"
    )

