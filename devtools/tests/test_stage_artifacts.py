from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import sys
import threading

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "stage_artifacts.py"


@pytest.fixture
def index_server():
    routes = {}
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            status, body = routes.get(self.path, (404, "Not found"))
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body.encode())

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/simple/", routes, requests
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


@pytest.fixture
def stage(tmp_path, index_server):
    source = tmp_path / "incoming"
    source.mkdir()
    destination = tmp_path / "dist"
    output = tmp_path / "output"

    def run(*filenames):
        for filename in filenames:
            (source / filename).write_bytes(b"wheel contents")
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--index-url",
                index_server[0],
                "--github-output",
                str(output),
                str(source),
                str(destination),
            ],
            capture_output=True,
            text=True,
        )
        return result, destination, output

    return run


def test_stages_only_missing_filenames_and_queries_each_project_once(
    stage, index_server
):
    # A version-only comparison would incorrectly skip the new platform wheel.
    index_server[1]["/simple/demo-pkg/"] = (
        200,
        """<html><body>
<a href="../../demo/demo_pkg-1.0-py3-none-any.whl#sha256=abc">existing</a>
<a href="https://example.test/demo_pkg-1.0%2Blocal-py3-none-any.whl?download=1#sha256=def">existing</a>
</body></html>""",
    )
    result, destination, output = stage(
        "demo_pkg-1.0-py3-none-any.whl",
        "demo_pkg-1.0+local-py3-none-any.whl",
        "demo_pkg-1.0-py3-none-linux_armv7l.whl",
    )
    assert result.returncode == 0, result.stderr
    assert sorted(p.name for p in destination.iterdir()) == [
        "demo_pkg-1.0-py3-none-linux_armv7l.whl"
    ]
    assert (
        destination / "demo_pkg-1.0-py3-none-linux_armv7l.whl"
    ).read_bytes() == b"wheel contents"
    assert output.read_text() == "count=1\n"
    assert index_server[2] == ["/simple/demo-pkg/"]


def test_missing_project_stages_wheel(stage):
    result, destination, output = stage("new_pkg-1.0-py3-none-any.whl")
    assert result.returncode == 0, result.stderr
    assert [p.name for p in destination.iterdir()] == ["new_pkg-1.0-py3-none-any.whl"]
    assert output.read_text() == "count=1\n"


def test_all_existing_is_successful_noop(stage, index_server):
    index_server[1]["/simple/demo/"] = (
        200,
        '<a href="demo-1.0-py3-none-any.whl">demo</a>',
    )
    result, destination, output = stage("demo-1.0-py3-none-any.whl")
    assert result.returncode == 0, result.stderr
    assert list(destination.iterdir()) == []
    assert output.read_text() == "count=0\n"


@pytest.mark.parametrize("status", [401, 403, 500])
def test_lookup_errors_fail_instead_of_staging(stage, index_server, status):
    index_server[1]["/simple/demo/"] = (status, "Error")
    result, destination, output = stage("demo-1.0-py3-none-any.whl")
    assert result.returncode != 0
    assert f"HTTP Error {status}" in result.stderr
    assert not list(destination.glob("*.whl"))
    assert not output.exists()


def test_empty_source_is_successful_noop(stage, index_server):
    result, destination, output = stage()
    assert result.returncode == 0, result.stderr
    assert list(destination.iterdir()) == []
    assert output.read_text() == "count=0\n"
    assert index_server[2] == []
