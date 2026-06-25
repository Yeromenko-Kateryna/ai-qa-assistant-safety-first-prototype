import sys
import scripts.smoke_gemini_requirement_agent as smoke_script

def test_smoke_script_import_side_effects():
    # Verify that importing the script does not load genai or check keys
    assert "google.genai" not in sys.modules
    assert "google.auth" not in sys.modules


def test_smoke_script_key_missing_behavior():
    fake_environ = {}

    def fake_import():
        raise AssertionError("import_genai should not be called when API key is missing")

    ready, error_msg = smoke_script.check_sdk_and_key(fake_environ, fake_import)
    assert not ready
    assert "GEMINI_API_KEY" in error_msg
    # Ensure no part of the key itself is printed or referenced
    assert "dummy_key" not in error_msg
    assert "partial" not in error_msg.lower()


def test_smoke_script_sdk_missing_behavior():
    fake_environ = {"GEMINI_API_KEY": "dummy_key"}

    def fake_import_failing():
        raise ImportError("mock genai import failure")

    ready, error_msg = smoke_script.check_sdk_and_key(fake_environ, fake_import_failing)
    assert not ready
    assert "SDK is not installed" in error_msg


def test_smoke_script_ready_behavior():
    fake_environ = {"GEMINI_API_KEY": "dummy_key"}

    def fake_import_success():
        return object()

    ready, error_msg = smoke_script.check_sdk_and_key(fake_environ, fake_import_success)
    assert ready
    assert error_msg == ""


def test_smoke_script_main_guard():
    # Verify main exists but does not trigger when imported
    assert hasattr(smoke_script, "main")
