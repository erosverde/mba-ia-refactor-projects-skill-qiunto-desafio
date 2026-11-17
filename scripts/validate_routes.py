"""Run the HTTP contract checks for all three projects."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CHECKS = Path(__file__).resolve().parent / "http_contract"


def run(command, project):
    cwd = ROOT / project
    env = os.environ.copy()
    env.pop("PYTHONOPTIMIZE", None)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, (str(cwd), env.get("PYTHONPATH"))))
    env["PYTHONUTF8"] = "1"
    print(f"\n== {project} ==", flush=True)
    subprocess.run(command, cwd=cwd, env=env, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shop-python", default=sys.executable, help="Python with code-smells-project dependencies")
    parser.add_argument("--task-python", default=sys.executable, help="Python with task-manager-api dependencies")
    parser.add_argument("--node", default="node", help="Node.js executable")
    args = parser.parse_args()

    try:
        run([args.shop_python, str(CHECKS / "shop.py")], "code-smells-project")
        run([args.node, str(CHECKS / "ecommerce.cjs")], "ecommerce-api-legacy")
        run([args.task_python, str(CHECKS / "tasks.py")], "task-manager-api")
    except subprocess.CalledProcessError as error:
        return error.returncode or 1
    except OSError as error:
        print(error, file=sys.stderr)
        return 1

    print("\nPASS: 44/44 contratos HTTP")
    return 0


if __name__ == "__main__":
    sys.exit(main())
