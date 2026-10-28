"""Проверить gitleaks на одноразовом репозитории без настоящих секретов."""

import argparse
import os
import secrets
import subprocess
import tempfile
from pathlib import Path


def verify(binary):
    with tempfile.TemporaryDirectory(prefix="devops-secrets-") as directory:
        root = Path(directory)
        env = os.environ | {
            "GIT_AUTHOR_NAME": "Test",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_EMAIL": "test@example.com",
        }

        def git(*args):
            return subprocess.run(
                ["git", *args], cwd=root, env=env, check=True, capture_output=True, text=True
            ).stdout.strip()

        def scan(expected):
            result = subprocess.run(
                [binary, "git", ".", "--redact", "--no-banner"],
                cwd=root,
                capture_output=True,
                text=True,
            )
            assert result.returncode == expected, result.stdout + result.stderr

        git("init", "-b", "main")
        (root / "README.md").write_text("Учебная проверка\n")
        git("add", ".")
        git("commit", "-m", "Clean baseline")
        clean = git("rev-parse", "HEAD")
        # Случайная строка создана только для проверки и нигде не используется.
        (root / "sample.env").write_text("DB_PASSWORD=" + secrets.token_hex(24) + "\n")
        git("add", ".")
        git("commit", "-m", "Synthetic secret")
        scan(1)
        print("Синтетический секрет в коммите: обнаружен")
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
    verify(parser.parse_args().binary)
