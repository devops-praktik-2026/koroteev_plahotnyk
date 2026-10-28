"""Два настоящих HTTP-сервиса с временными базами и миграциями."""

import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from smoke import check  # noqa: E402


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_ready(base, process):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError(f"Сервис завершился с кодом {process.returncode}")
        try:
            with urllib.request.urlopen(base + "/health", timeout=0.5) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.1)
    raise AssertionError(f"Сервис не запустился: {base}")


def test_real_services_and_outage(tmp_path):
    accounts_port, orders_port = free_port(), free_port()
    accounts = f"http://127.0.0.1:{accounts_port}"
    orders = f"http://127.0.0.1:{orders_port}"
    processes = []
    try:
        for service, port in [("accounts", accounts_port), ("orders", orders_port)]:
            env = os.environ | {
                "DATABASE_URL": f"sqlite:///{tmp_path / (service + '.db')}",
                "ACCOUNTS_URL": accounts,
                "ACCOUNTS_TIMEOUT_SECONDS": "0.5",
            }
            cwd = ROOT / "services" / service
            subprocess.run(
                [sys.executable, "-m", "alembic", "upgrade", "head"], cwd=cwd, env=env, check=True
            )
            # Повторное применение не должно менять схему или терять данные.
            subprocess.run(
                [sys.executable, "-m", "alembic", "upgrade", "head"], cwd=cwd, env=env, check=True
            )
            with (tmp_path / f"{service}.log").open("w") as log:
                process = subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "uvicorn",
                        f"{service}.main:app",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(port),
                    ],
                    cwd=cwd,
                    env=env,
                    stdout=log,
                    stderr=log,
                )
            processes.append(process)
            wait_ready(f"http://127.0.0.1:{port}", process)
        check(accounts, orders)
        processes[0].terminate()
        processes[0].wait(timeout=5)
        check(accounts, orders, unavailable=True)
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


def test_migrations_share_database_and_orders_can_be_recreated(tmp_path):
    from sqlalchemy import create_engine, inspect

    env = os.environ | {"DATABASE_URL": f"sqlite:///{tmp_path / 'shared.db'}"}

    def migrate(service, *args):
        subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            cwd=ROOT / "services" / service,
            env=env,
            check=True,
        )

    migrate("accounts", "upgrade", "head")
    migrate("orders", "upgrade", "head")
    engine = create_engine(env["DATABASE_URL"])
    try:
        assert {"accounts", "orders", "alembic_version", "alembic_version_orders"} <= set(
            inspect(engine).get_table_names()
        )
        migrate("orders", "downgrade", "base")
        assert "orders" not in inspect(engine).get_table_names()
        assert "accounts" in inspect(engine).get_table_names()
        migrate("orders", "upgrade", "head")
        assert "orders" in inspect(engine).get_table_names()
    finally:
        engine.dispose()
