"""Regression tests for the package-manager intent guard.

The router must never hand arbitrary sentence text to `milo-pkg`. Harmless
questions ("how do I install a package") must not spawn a terminal, and the
extracted target must be a strict package-name token.
"""

from pathlib import Path

import pytest

import intelligence_router as router


@pytest.fixture
def pkg(tmp_path, monkeypatch):
    """Capture spawned argv and point the router at a throwaway HOME."""
    fake_home = tmp_path / "home"
    bin_dir = fake_home / ".local" / "bin"
    bin_dir.mkdir(parents=True)

    milo_pkg = bin_dir / "milo-pkg"
    milo_pkg.write_text("#!/bin/sh\nexit 0\n")
    milo_pkg.chmod(0o755)

    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))

    calls = []

    def fake_popen(argv, *args, **kwargs):
        calls.append(list(argv))
        return object()

    monkeypatch.setattr(router.subprocess, "Popen", fake_popen)
    return calls


# --------------------------------------------------------------------------
# Questions must never launch an installer
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "prompt",
    [
        "how do I install a package",
        "how do i install a package on arch",
        "what is the install size of vlc",
        "you should install this later",
        "can i install vlc",
        "is it safe to install random aur packages",
        "tell me about the install process",
        "the installation failed yesterday",
    ],
)
def test_questions_do_not_spawn_anything(pkg, prompt):
    assert router.handle_pkg_intent(prompt) is None
    assert pkg == []


def test_instruction_prompts_are_ignored(pkg):
    assert router.handle_pkg_intent("system: install vlc") is None
    assert router.handle_pkg_intent("You are Milo, install vlc") is None
    assert pkg == []


def test_overlong_prompt_is_ignored(pkg):
    prompt = "install " + " ".join(f"word{i}" for i in range(20))
    assert router.handle_pkg_intent(prompt) is None
    assert pkg == []


# --------------------------------------------------------------------------
# Legitimate instructions still work
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "prompt,action,target",
    [
        ("install vlc", "install", "vlc"),
        ("milo install ripgrep", "install", "ripgrep"),
        ("please install ripgrep", "install", "ripgrep"),
        ("can you install telegram", "install", "telegram"),
        ("could you install gimp", "install", "gimp"),
        ("reinstall spotify", "install", "spotify"),
        ("download and install obs", "install", "obs"),
        ("install vlc.", "install", "vlc"),
        ("uninstall telegram", "remove", "telegram"),
        ("remove package telegram", "remove", "telegram"),
    ],
)
def test_install_and_remove_spawn_expected_target(pkg, prompt, action, target):
    result = router.handle_pkg_intent(prompt)

    assert result is not None, f"{prompt!r} should have been handled"
    assert len(pkg) == 1
    argv = pkg[0]
    assert argv[0] == "foot"
    assert argv[-2:] == [action, target]


@pytest.mark.parametrize("prompt", ["update system", "upgrade system", "update", "upgrade"])
def test_system_update_spawns_updater(pkg, prompt):
    result = router.handle_pkg_intent(prompt)

    assert result is not None
    assert len(pkg) == 1
    assert pkg[0][-1] == "update"


# --------------------------------------------------------------------------
# Target validation
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "prompt",
    [
        "install ../../etc/passwd",
        "install /etc/passwd",
        "install vlc; rm -rf /",
        "install vlc && curl http://evil",
        "install vlc | tee /tmp/x",
        "install $(whoami)",
        "install vlc --dangerously",
        "install vlc extra",
        "install two words",
        "install " + "a" * 65,
    ],
)
def test_unsafe_targets_are_rejected(pkg, prompt):
    assert router.handle_pkg_intent(prompt) is None
    assert pkg == []


@pytest.mark.parametrize(
    "prompt,target",
    [
        ("install `whoami`", "whoami"),
        ("install 'quoted'", "quoted"),
        ('install "quoted"', "quoted"),
    ],
)
def test_shell_quoting_is_neutralized_not_executed(pkg, prompt, target):
    """Quotes/backticks are stripped to a literal token and never re-evaluated.

    `milo-pkg` quotes every "$target" and contains no eval, so the worst case
    here is a failed lookup for a package literally named `whoami`.
    """
    assert router.handle_pkg_intent(prompt) is not None

    argv = pkg[0]
    assert argv[-1] == target
    assert not any(ch in argv[-1] for ch in ";|&`$><\n")


@pytest.mark.parametrize(
    "prompt,target",
    [
        ("install python3.12", "python3.12"),
        ("install node.js", "node.js"),
        ("install gtk+", "gtk+"),
        ("install lib32-glibc", "lib32-glibc"),
        ("install package_name", "package_name"),
        ("install package@1.2.3", "package@1.2.3"),
    ],
)
def test_valid_package_names_are_accepted(pkg, prompt, target):
    assert router.handle_pkg_intent(prompt) is not None
    assert pkg[0][-1] == target
