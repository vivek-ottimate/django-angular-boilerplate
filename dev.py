"""Set up and run the project with one command.

Usage:
    uv run dev.py              set everything up, then start Django and Angular together
    uv run dev.py check        set everything up and confirm it all works
    uv run dev.py agy          start Antigravity CLI (extra arguments are passed through)
    uv run dev.py npm ...      run npm in frontend/ with the project's Node.js

uv provides Python 3.12 and the Python packages. This script adds Node.js when the installed one
is missing or too old, installs the frontend packages and Antigravity CLI, and runs both servers.
Anything it downloads goes into .tools/ inside the repo.
"""

import hashlib
import io
import json
import os
import platform
import shutil
import signal
import socket
import subprocess
import sys
import tarfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
TOOLS = ROOT / ".tools"
NODE_DIR = TOOLS / "node"
AGY_DIR = TOOLS / "agy"
NG = FRONTEND / "node_modules" / "@angular" / "cli" / "bin" / "ng.js"
NODE_VERSION = "22.23.3"
AGY_MANIFESTS = "https://antigravity-cli-auto-updater-974169037036.us-central1.run.app/manifests"
IS_WINDOWS = platform.system() == "Windows"
HOST = "0.0.0.0" if os.environ.get("CODESPACES") == "true" else "127.0.0.1"
DJANGO_PORT = 8000
ANGULAR_PORT = 4200
QUIET_NPM = ["--no-audit", "--no-fund", "--loglevel=error"]


def tool_dirs():
    """Return the .tools directories that hold the node and agy executables."""
    if IS_WINDOWS:
        return [NODE_DIR / "Scripts", AGY_DIR]
    return [NODE_DIR / "bin", AGY_DIR]


def agy_install_dirs():
    """Return where Antigravity CLI's official installers put agy, in case it isn't on PATH yet."""
    if IS_WINDOWS:
        return [Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "agy" / "bin"]
    return [Path.home() / ".local" / "bin"]


ENV = os.environ.copy()
ENV["PATH"] = os.pathsep.join([*map(str, tool_dirs()), ENV.get("PATH", ""), *map(str, agy_install_dirs())])
ENV["NG_CLI_ANALYTICS"] = "false"
ENV["PYTHONUNBUFFERED"] = "1"


class SetupError(Exception):
    """A setup step failed in a way the candidate needs to see."""


def say(message):
    print(f"==> {message}", flush=True)


def which(name):
    return shutil.which(name, path=ENV["PATH"])


def run(cmd, cwd=ROOT, quiet=False):
    """Run a command with the project's PATH, raising SetupError if it fails."""
    result = subprocess.run(
        [str(part) for part in cmd],
        cwd=cwd,
        env=ENV,
        stdout=subprocess.PIPE if quiet else None,
        stderr=subprocess.STDOUT if quiet else None,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        output = f"\n{result.stdout.strip()}" if quiet and result.stdout else ""
        raise SetupError(f"'{' '.join(map(str, cmd))}' failed{output}")
    return result.stdout if quiet else ""


def node_version():
    """Return the (major, minor) version of the node on PATH, or None if there is none that runs."""
    node = which("node")
    if not node:
        return None
    try:
        text = subprocess.run([node, "--version"], capture_output=True, text=True, env=ENV, timeout=30).stdout
        major, minor = text.strip().lstrip("v").split(".")[:2]
        return int(major), int(minor)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None


def node_supported(version):
    """Angular 21 needs Node ^20.19, ^22.12 or >=24."""
    if not version:
        return False
    major, minor = version
    return (major == 20 and minor >= 19) or (major == 22 and minor >= 12) or major >= 24


def ensure_node():
    """Use the installed Node.js if Angular supports it, otherwise download one into .tools/node."""
    version = node_version()
    if node_supported(version):
        return
    found = "none found" if not version else f"found {version[0]}.{version[1]}, which is too old"
    say(f"Downloading Node.js {NODE_VERSION} into .tools/node ({found})")
    shutil.rmtree(NODE_DIR, ignore_errors=True)
    run([sys.executable, "-m", "nodeenv", "--prebuilt", f"--node={NODE_VERSION}", NODE_DIR], quiet=True)
    if not node_supported(node_version()):
        raise SetupError("Node.js was downloaded but does not run")


def ensure_frontend_packages():
    """Install the frontend packages from the lockfile when they are missing or out of date."""
    marker = FRONTEND / "node_modules" / ".package-lock.json"
    lockfile = FRONTEND / "package-lock.json"
    if marker.exists() and NG.exists() and marker.stat().st_mtime + 1 >= lockfile.stat().st_mtime:
        return
    say("Installing frontend packages (first run takes a minute or two)")
    run([which("npm"), "ci", *QUIET_NPM], cwd=FRONTEND)


def agy_command():
    """Return the path of a working Antigravity CLI, or None."""
    agy = which("agy")
    if not agy:
        return None
    try:
        result = subprocess.run([agy, "--version"], capture_output=True, env=ENV, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return agy if result.returncode == 0 else None


def agy_release():
    """Return the release name for this machine, chosen the way the official installers choose it."""
    arch = "arm64" if platform.machine().lower() in ("arm64", "aarch64") else "amd64"
    if IS_WINDOWS:
        return f"windows_{arch}"
    if platform.system() == "Darwin":
        return f"darwin_{arch}"
    musl = any(Path(f"/lib/libc.musl-{name}.so.1").exists() for name in ("x86_64", "aarch64"))
    return f"linux_{arch}_musl" if musl else f"linux_{arch}"


def download_agy():
    """Download agy into .tools/agy and verify it against the release manifest's SHA-512."""
    try:
        with urllib.request.urlopen(f"{AGY_MANIFESTS}/{agy_release()}.json", timeout=30) as response:
            manifest = json.load(response)
        with urllib.request.urlopen(manifest["url"], timeout=600) as response:
            payload = response.read()
    except (OSError, ValueError, KeyError) as error:
        raise SetupError(
            f"could not download Antigravity CLI ({error}). Install it with the official one-liner instead:\n"
            "  macOS/Linux:         curl -fsSL https://antigravity.google/cli/install.sh | bash\n"
            "  Windows PowerShell:  irm https://antigravity.google/cli/install.ps1 | iex"
        ) from None
    if hashlib.sha512(payload).hexdigest() != manifest["sha512"].lower():
        raise SetupError("the Antigravity CLI download is corrupted (checksum mismatch); run this again")
    if manifest["url"].endswith(".tar.gz"):
        with tarfile.open(fileobj=io.BytesIO(payload)) as archive:
            payload = archive.extractfile("antigravity").read()
    AGY_DIR.mkdir(parents=True, exist_ok=True)
    binary = AGY_DIR / ("agy.exe" if IS_WINDOWS else "agy")
    binary.write_bytes(payload)
    binary.chmod(0o755)


def ensure_agy():
    """Use the installed Antigravity CLI if it works, otherwise download one into .tools/agy."""
    agy = agy_command()
    if agy:
        return agy
    say("Downloading Antigravity CLI into .tools/agy")
    download_agy()
    agy = agy_command()
    if not agy:
        raise SetupError("Antigravity CLI was downloaded but does not run")
    return agy


def agy_signed_in(agy):
    """Return True if agy can list its models, which it only does once signed in."""
    try:
        result = subprocess.run([agy, "models"], capture_output=True, stdin=subprocess.DEVNULL, env=ENV, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def migrate():
    run([sys.executable, "manage.py", "migrate", "-v", "0"], cwd=BACKEND)


def setup():
    ensure_node()
    ensure_frontend_packages()
    ensure_agy()
    migrate()


def port_in_use(port):
    with socket.socket() as sock:
        sock.settimeout(1)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def busy_ports():
    return [port for port in (DJANGO_PORT, ANGULAR_PORT) if port_in_use(port)]


def start_process(cmd, cwd):
    """Start a server process in its own process group so it can be stopped as a whole."""
    options = {"start_new_session": True} if not IS_WINDOWS else {}
    return subprocess.Popen(
        [str(part) for part in cmd],
        cwd=cwd,
        env=ENV,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        **options,
    )


def stop_process(process):
    """Stop a server process and everything it started."""
    if process.poll() is not None:
        return
    if IS_WINDOWS:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True)
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=10)
        except ProcessLookupError:
            return
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
    process.wait()


def pump(process, label, sink):
    """Forward a process's output line by line, labelled, to ``sink``."""
    for line in process.stdout:
        sink(f"[{label}] {line.rstrip()}")


def start_servers(reload=True):
    """Start Django and the Angular dev server; return the two processes."""
    django_cmd = [sys.executable, "manage.py", "runserver", f"{HOST}:{DJANGO_PORT}"]
    if not reload:
        django_cmd.append("--noreload")
    django = start_process(django_cmd, BACKEND)
    angular = start_process([which("node"), NG, "serve", "--host", HOST, "--port", ANGULAR_PORT], FRONTEND)
    return django, angular


def serve():
    """Set up, then run both servers until Ctrl+C or until one of them exits."""
    setup()
    busy = busy_ports()
    if busy:
        raise SetupError(f"port {' and '.join(map(str, busy))} already in use; stop whatever is running there first")
    django, angular = start_servers()
    lock = threading.Lock()

    def sink(line):
        with lock:
            print(line, flush=True)

    for process, label in ((django, "django"), (angular, "angular")):
        threading.Thread(target=pump, args=(process, label, sink), daemon=True).start()
    say(f"Django: http://localhost:{DJANGO_PORT}   Angular: http://localhost:{ANGULAR_PORT}   (Ctrl+C stops both)")
    try:
        while django.poll() is None and angular.poll() is None:
            time.sleep(0.5)
        say("A server stopped; stopping the other one")
    except KeyboardInterrupt:
        say("Stopping")
    finally:
        stop_process(django)
        stop_process(angular)


def fetch(url):
    """Return (status, body) for a GET request, or (None, error text) if nothing answered."""
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        return error.code, ""
    except OSError as error:
        return None, str(error)


def servers_respond():
    """Start both servers, wait for Angular to proxy /api/hello/ to Django, then stop them."""
    django, angular = start_servers(reload=False)
    logs = {"django": [], "angular": []}
    for process, label in ((django, "django"), (angular, "angular")):
        threading.Thread(target=pump, args=(process, label, logs[label].append), daemon=True).start()
    try:
        deadline = time.time() + 240
        while time.time() < deadline:
            if django.poll() is not None or angular.poll() is not None:
                break
            status, body = fetch(f"http://127.0.0.1:{ANGULAR_PORT}/api/hello/")
            if status == 200 and "message" in body:
                status, _ = fetch(f"http://127.0.0.1:{ANGULAR_PORT}/")
                if status == 200:
                    return None
            time.sleep(1)
        tail = "\n".join(logs["django"][-15:] + logs["angular"][-15:])
        return f"the servers did not answer within 4 minutes\n{tail}"
    finally:
        stop_process(django)
        stop_process(angular)


def check():
    """Set everything up, then confirm each piece works. Exits non-zero if anything failed."""
    results = []

    def record(status, name, detail=""):
        results.append((status, name, detail))
        print(f"  {status:<5} {name}{'  ' + detail if detail else ''}", flush=True)

    say("Setting up (the first run downloads and installs everything)")
    try:
        setup()
    except SetupError as error:
        print(f"\nSetup failed: {error}", flush=True)
        sys.exit(1)

    print("\nSetup check", flush=True)
    record("OK", f"Python {platform.python_version()}")
    import django

    record("OK", f"Django {django.get_version()}")
    major, minor = node_version()
    source = "project copy in .tools/node" if which("node").startswith(str(NODE_DIR)) else "installed on this machine"
    record("OK", f"Node.js {major}.{minor}", f"({source})")
    record("OK", "Frontend packages installed")
    agy = agy_command()
    version = subprocess.run([agy, "--version"], capture_output=True, text=True, env=ENV).stdout.strip()
    record("OK", f"Antigravity CLI {version}")
    if agy_signed_in(agy):
        record("OK", "Antigravity CLI signed in")
    else:
        record("WARN", "Antigravity CLI not signed in yet", "run 'uv run dev.py agy' and sign in with Google")
    try:
        hashlib.scrypt(b"check", salt=b"check", n=2, r=1, p=1)
        record("OK", "Interview runner works")
    except (AttributeError, ValueError) as error:
        record("FAIL", "Interview runner", str(error))
    try:
        run([sys.executable, "manage.py", "test", "-v", "0"], cwd=BACKEND, quiet=True)
        record("OK", "Django tests pass")
    except SetupError as error:
        record("FAIL", "Django tests", str(error))
    busy = busy_ports()
    if busy:
        ports = " and ".join(map(str, busy))
        record("FAIL", f"Port {ports} already in use", "stop whatever is running there, then run this check again")
    else:
        problem = servers_respond()
        if problem:
            record("FAIL", "Servers start and talk to each other", problem)
        else:
            record("OK", "Servers start and talk to each other")

    failed = [r for r in results if r[0] == "FAIL"]
    if failed:
        print(f"\n{len(failed)} problem(s) found. Fix them, then run 'uv run dev.py check' again.", flush=True)
        sys.exit(1)
    print("\nAll set. Start the project with: uv run dev.py", flush=True)


def passthrough(tool, args):
    """Run Antigravity CLI from the repo root, or npm in frontend/ with the project's Node.js."""
    if tool == "agy":
        command, cwd = ensure_agy(), ROOT
    else:
        ensure_node()
        command, cwd = which("npm"), FRONTEND
    try:
        return subprocess.run([command, *args], cwd=cwd, env=ENV).returncode
    except KeyboardInterrupt:
        return 130


def main():
    sys.stdout.reconfigure(errors="replace")
    args = sys.argv[1:]
    command = args[0] if args else "start"
    try:
        if command == "start":
            serve()
        elif command == "check":
            check()
        elif command in ("agy", "npm"):
            sys.exit(passthrough(command, args[1:]))
        else:
            print(__doc__)
            sys.exit(2)
    except SetupError as error:
        print(f"\nError: {error}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
