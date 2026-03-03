"""
Templates menu API: list templates and create notebook from template.
Served under /templates-menu/ (see __init__.py for mount).
"""
import json
import os
import shutil
from pathlib import Path

from tornado import web

from jupyter_server.base.handlers import APIHandler

# Default directory with .ipynb templates (overridable via env)
TEMPLATES_DIR = os.environ.get("JUPYTER_TEMPLATES_DIR", "/opt/notebook-templates")


def _path_under(base: Path, subpath: str) -> Path | None:
    """Resolve base/subpath; return None if the result escapes base (path traversal)."""
    if not subpath or ".." in subpath or Path(subpath).is_absolute():
        return None
    try:
        base_res = base.resolve()
        resolved = (base_res / subpath).resolve()
        if not resolved.is_relative_to(base_res):
            return None
        return resolved
    except (ValueError, OSError):
        return None


def _list_templates():
    """Return list of {id, label} for each .ipynb under TEMPLATES_DIR."""
    out = []
    if not os.path.isdir(TEMPLATES_DIR):
        return out
    for root, _dirs, files in os.walk(TEMPLATES_DIR):
        for f in files:
            if f.endswith(".ipynb"):
                rel = os.path.relpath(os.path.join(root, f), TEMPLATES_DIR)
                id_ = rel.replace(os.sep, "/")
                label = os.path.splitext(os.path.basename(f))[0].replace("_", " ").replace("-", " ").title()
                out.append({"id": id_, "label": label})
    return sorted(out, key=lambda x: x["label"])


class TemplatesListHandler(APIHandler):
    """GET /templates-menu/templates -> list of {id, label}."""

    @web.authenticated
    def get(self):
        self.finish(json.dumps(_list_templates()))


def _cwd_under_root(root_dir: str, cwd_arg: str) -> Path:
    """Resolve cwd_arg under root_dir; return root_dir path if invalid or traversal."""
    root = Path(root_dir).resolve()
    if not cwd_arg or cwd_arg.strip() == ".":
        return root
    arg = cwd_arg.strip().lstrip("/").replace("\\", "/")
    if ".." in arg or Path(arg).is_absolute():
        return root
    try:
        resolved = (root / arg).resolve()
        if resolved.is_dir() and resolved.is_relative_to(root):
            return resolved
    except (ValueError, OSError):
        pass
    return root


class TemplatesCreateHandler(APIHandler):
    """POST /templates-menu/create with JSON {template_id} -> copy to cwd and return path."""

    @web.authenticated
    def post(self):
        try:
            body = json.loads(self.request.body or "{}")
            template_id = body.get("template_id")
            if not template_id or not isinstance(template_id, str):
                self.set_status(400)
                self.finish(json.dumps({"error": "invalid template_id"}))
                return
            templates_base = Path(TEMPLATES_DIR)
            src_path = _path_under(templates_base, template_id)
            if src_path is None or not src_path.is_file():
                self.set_status(404)
                self.finish(json.dumps({"error": "template not found"}))
                return
            root_dir = getattr(
                getattr(self, "contents_manager", None), "root_dir", None
            ) or self.settings.get("server_root_dir") or os.path.expanduser("~")
            cwd_arg = self.get_query_argument("cwd", "").strip() or "."
            cwd = _cwd_under_root(root_dir, cwd_arg)
            dest_name = src_path.name
            dest = cwd / dest_name
            base, ext = os.path.splitext(dest_name)
            n = 0
            while dest.exists():
                n += 1
                dest = cwd / f"{base}_{n}{ext}"
            shutil.copy2(src_path, dest)
            rel_path = dest.relative_to(cwd).as_posix()
            self.finish(json.dumps({"path": rel_path}))
        except json.JSONDecodeError:
            self.set_status(400)
            self.finish(json.dumps({"error": "invalid request body"}))
        except Exception as e:
            self.log.debug("Templates create error: %s", e, exc_info=True)
            self.set_status(500)
            self.finish(json.dumps({"error": "Failed to create notebook from template"}))
