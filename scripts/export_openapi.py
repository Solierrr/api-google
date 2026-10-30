import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.main import app  # noqa: E402
from app.openapi import build_openapi  # noqa: E402

RELEASE_MARKER = "  # x-release-please-version"


def render() -> str:
    """Contrato completo (com as rotas `/internal/`) em YAML, com a marca do release-please na versão"""
    text = yaml.safe_dump(build_openapi(app, include_internal=True), sort_keys=False, allow_unicode=True, width=120)
    version_line = f"  version: {app.version}\n"
    return text.replace(version_line, version_line.rstrip("\n") + RELEASE_MARKER + "\n", 1)


if __name__ == "__main__":
    (ROOT / "openapi.yaml").write_text(render(), encoding="utf-8", newline="\n")
