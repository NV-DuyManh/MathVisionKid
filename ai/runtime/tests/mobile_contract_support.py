"""Run mobile contract assertions against the installed TypeScript helpers."""
import json
import subprocess
from pathlib import Path

MOBILE_ROOT = Path(__file__).resolve().parents[3] / "apps" / "student-mobile"
LINE_REVIEW = "./src/features/recognition/utils/lineReview.ts"


def run_mobile_node(script: str):
    # Use the app's compiler so relative .ts imports behave like the real app build.
    bootstrap = """
const ts = require('typescript');
const fs = require('node:fs');
const options = { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true };
require.extensions['.ts'] = (module, filename) => {
  module._compile(ts.transpileModule(fs.readFileSync(filename, 'utf8'), { compilerOptions: options }).outputText, filename);
};
"""
    compiled = "eval(ts.transpileModule(" + json.dumps(script, ensure_ascii=False) + ", {compilerOptions: options}).outputText);"
    return subprocess.run(["node", "-"], input=bootstrap + compiled, cwd=MOBILE_ROOT,
                          capture_output=True, text=True, encoding="utf-8", timeout=30)


def mobile_helper(function: str, *args):
    script = f"const helpers = require({json.dumps(LINE_REVIEW)}); console.log(JSON.stringify(helpers[{json.dumps(function)}](...{json.dumps(args, ensure_ascii=False)})));"
    result = run_mobile_node(script)
    assert result.returncode == 0, result.stderr + result.stdout
    return json.loads(result.stdout)


def run_legacy_matrix(path: Path):
    script = path.read_text(encoding="utf-8").replace("../../features/recognition/utils/lineReview.ts", LINE_REVIEW)
    return run_mobile_node(script)
