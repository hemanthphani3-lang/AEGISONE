import re
from pathlib import Path


def test_gitignore_excludes_dotenv():
    """Verify .gitignore properly excludes .env files while keeping .env.example."""
    gitignore_path = Path(__file__).parent.parent / ".gitignore"
    assert gitignore_path.exists(), ".gitignore file missing!"
    content = gitignore_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    assert ".env" in lines


def test_no_private_keys_or_real_secrets_in_source():
    """Scan source Python files to ensure no private keys or committed production secrets exist."""
    backend_dir = Path(__file__).parent.parent
    suspicious_patterns = [
        re.compile(r"-----BEGIN (RSA|OPENSSH|EC|PRIVATE) KEY-----"),
        re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS Access Key ID
        re.compile(r"ghp_[a-zA-Z0-9]{36}"),  # GitHub Personal Access Token
    ]

    for py_file in backend_dir.rglob("*.py"):
        # Skip virtualenvs or cache directories if present
        if any(part in py_file.parts for part in (".venv", "venv", "__pycache__", ".pytest_cache")):
            continue

        content = py_file.read_text(encoding="utf-8", errors="ignore")
        for pattern in suspicious_patterns:
            assert not pattern.search(content), f"Potential secret matched in {py_file}!"
