import subprocess
import json


def test_agent_uses_read_file():
    result = subprocess.run(
        ["uv", "run", "agent.py", "How do you resolve a merge conflict?"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert "answer" in output
    tools_used = [tc["tool"] for tc in output["tool_calls"]]
    assert "read_file" in tools_used
    assert "wiki/" in output.get("source", "")


def test_agent_uses_list_files():
    result = subprocess.run(
        ["uv", "run", "agent.py", "What files are in the wiki directory?"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert "answer" in output
    assert "tool_calls" in output
