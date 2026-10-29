"""Проверить поиск секретов в одноразовом репозитории с учебными данными."""

import argparse
import os
import secrets
import subprocess
import tempfile
from pathlib import Path


def verify(binary: str) -> None:
    """Проверить чистую историю, добавление секрета и удаление его файла."""
    with tempfile.TemporaryDirectory(prefix="devops-secrets-") as directory:
        root = Path(directory)
        env = os.environ | {
            "GIT_AUTHOR_NAME": "Test",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_EMAIL": "test@example.com",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
        }

        def git(*args: str) -> str:
            return subprocess.run(
                ["git", *args], cwd=root, env=env, check=True, capture_output=True, text=True
            ).stdout.strip()

        def scan(expected: int) -> None:
            result = subprocess.run(
                [binary, "git", ".", "--redact", "--no-banner"],
                cwd=root,
                capture_output=True,
                text=True,
            )
            if result.returncode != expected:
                raise RuntimeError(
                    f"Ожидался код {expected}, получен {result.returncode}:\n"
                    + result.stdout
                    + result.stderr
                )

        git("init", "-b", "main")
        (root / "README.md").write_text("Учебная проверка\n", encoding="utf-8")
        git("add", ".")
        git("commit", "-m", "Clean baseline")
        clean = git("rev-parse", "HEAD")
        scan(0)
        print("Чистая история: секретов нет")

        # Случайная строка используется только для проверки и не даёт никуда доступа.
        (root / "sample.env").write_text(
            "DB_PASSWORD=" + secrets.token_hex(24) + "\n", encoding="utf-8"
        )
        git("add", ".")
        git("commit", "-m", "Synthetic secret")
        scan(1)
        print("Учебный секрет в коммите: обнаружен")

        git("rm", "sample.env")
        git("commit", "-m", "Remove synthetic secret")
        scan(1)
        print("Файл удалён, секрет остался в истории: обнаружен")

        git("reset", "--hard", clean)
        scan(0)
        print("Одноразовая история очищена: секретов нет")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", help="Абсолютный путь к gitleaks")
    verify(str(Path(parser.parse_args().binary).resolve(strict=True)))
