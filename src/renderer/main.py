"""CPU-only CLI. No server, model, candidate ranking or dataset preparation."""
import argparse
import os
import signal
from pathlib import Path
import subprocess
import time

from .utils import RENDERER, ROOT, compile_design, read, write
from .exps import export_development, preset


def node_runtime():
    override = os.environ.get("CANVAS_RENDER_NODE")
    node = Path(override) if override else ROOT / "build/renderer_tooling/node-v24.20.0-linux-x64/bin/node"
    if not node.is_file():
        raise FileNotFoundError("Install the isolated runtime with src/renderer/scripts/setup.sh")
    return node


def render(evidence_path, design_path, output):
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError("Do not overwrite previews; choose a new output directory")
    evidence, design = read(evidence_path), read(design_path)
    compiled = compile_design(evidence, design)
    bundle = RENDERER / "web/dist/render.mjs"
    if not bundle.exists():
        raise FileNotFoundError("Web renderer not built; run setup.sh")
    output.mkdir(parents=True)
    write(output / "evidence.json", evidence)
    write(output / "design.json", design)
    write(output / "geometry.json", compiled)
    env = dict(os.environ, PLAYWRIGHT_BROWSERS_PATH=str(ROOT / "build/renderer_tooling/browsers"))
    started = time.monotonic()
    process = subprocess.Popen([str(node_runtime()), str(bundle), str(output)], cwd=RENDERER / "web", env=env,
                               start_new_session=True)
    try:
        code = process.wait(timeout=90)
        if code:
            raise subprocess.CalledProcessError(code, process.args)
    except BaseException as exc:
        # Stop only this invocation's child group; never touch inference services.
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=5)
        except ProcessLookupError:
            pass
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        if not (output / "manifest.json").exists():
            write(output / "manifest.json", {"status": "failed", "error": str(exc), "phase": "browser_runtime"})
        raise
    report = read(output / "manifest.json")
    from .gates import source_fingerprint
    report["renderer_source"] = source_fingerprint()
    report["python_end_to_end_seconds"] = round(time.monotonic()-started, 3)
    write(output / "manifest.json", report)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("render")
    r.add_argument("--evidence", required=True)
    r.add_argument("--design", required=True)
    r.add_argument("--out", required=True)
    e = sub.add_parser("export-development")
    e.add_argument("--index", type=int, choices=range(3), required=True)
    e.add_argument("--out", required=True)
    d = sub.add_parser("preset")
    d.add_argument("--evidence", required=True)
    d.add_argument("--name", choices=["operations", "relations_first", "matrix", "pairs"], default="operations")
    d.add_argument("--out", required=True)
    o = sub.add_parser("operate")
    o.add_argument("--evidence", required=True)
    o.add_argument("--design", required=True)
    o.add_argument("--operations", required=True)
    o.add_argument("--out", required=True)
    args = p.parse_args()
    if args.command == "render":
        report = render(args.evidence, args.design, args.out)
        print(f"PASS {args.out}: {report['card_count']} cards, {report['binding_count']} bindings, {report['python_end_to_end_seconds']}s")
    elif args.command == "export-development":
        evidence, audit = export_development(args.index)
        directory = Path(args.out)
        if directory.exists():
            raise FileExistsError(directory)
        write(directory / "evidence.json", evidence)
        write(directory / "source_audit.json", audit)
        for name in ("operations", "relations_first", "matrix"):
            write(directory / (name+".json"), preset(evidence, name))
        print(f"Exported {len(evidence['cards'])} cards; source coverage audit is separate from model-visible HTML")
    elif args.command == "operate":
        from .operations import apply_operations
        result, audit = apply_operations(read(args.evidence), read(args.design), read(args.operations))
        write(args.out, result)
        write(str(args.out)+".operations_audit.json", audit)
    else:
        write(args.out, preset(read(args.evidence), args.name))


if __name__ == "__main__":
    main()
