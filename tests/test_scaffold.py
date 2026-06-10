import subprocess
import sys
from pathlib import Path
import ast
import pytest


def _run_copier(template_path: Path, dest: Path, project_name: str = "testproj") -> None:
    cmd = [
        "copier",
        "copy",
        str(template_path),
        str(dest),
        "-f",
        "-d",
        f"project_name={project_name}",
        "-d",
        "python_version=3.13.6",
        "-d",
        "description=testing",
    ]
    # Use check=True so failures raise and fail the test.
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=120)


def test_copier_creates_expected_files(tmp_path: Path):
    """Run copier against the local template and assert basic files are rendered."""
    template_root = Path(__file__).resolve().parent.parent
    dest = tmp_path / "out"
    _run_copier(template_root, dest, project_name="testproj")

    # Basic files
    assert (dest / "pyproject.toml").exists(), "pyproject.toml should be created"
    assert (dest / "README.md").exists(), "README.md should be created"

    pyproject_text = (dest / "pyproject.toml").read_text()
    assert "testproj" in pyproject_text


def test_generated_package_init_is_valid_python(tmp_path: Path):
    """Find a package under src and ensure its __init__.py parses as valid Python."""
    template_root = Path(__file__).resolve().parent.parent
    dest = tmp_path / "out2"
    _run_copier(template_root, dest, project_name="tutu")

    src_dir = dest / "src"
    assert src_dir.exists(), "src directory should exist in generated project"

    # Find candidate package directories under src
    pkgs = [p for p in src_dir.iterdir() if p.is_dir()]
    assert pkgs, "No package directories found under src"

    # Ensure at least one package has a valid __init__.py
    init_found = False
    for pkg in pkgs:
        init = pkg / "__init__.py"
        if not init.exists():
            continue
        init_found = True
        try:
            ast.parse(init.read_text())
        except Exception as exc:
            pytest.fail(f"__init__.py in {pkg.name} is not valid Python: {exc}")

    assert init_found, "No __init__.py files found in any package under src"
