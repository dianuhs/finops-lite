def test_package_imports():
    __import__("finops_lite")

def test_cli_help_exit_zero():
    import subprocess, sys
    # use module form so it works even if the console script isn't installed
    r = subprocess.run(
        [sys.executable, "-m", "finops_lite.cli", "--help"],
        capture_output=True, text=True
    )
    assert r.returncode == 0
    assert "usage" in r.stdout.lower()
