import subprocess
import json


def test_agent_reads_source_code():
    result = subprocess.run(
        ["uv", "run", "agent.py", "What framework does the backend use?"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert "answer" in output
    tools_used = [tc["tool"] for tc in output["tool_calls"]]
    assert "read_file" in tools_used


def test_agent_queries_api():
    result = subprocess.run(
        ["uv", "run", "agent.py", "How many items are in the database?"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert "answer" in output
    tools_used = [tc["tool"] for tc in output["tool_calls"]]
    assert "query_api" in tools_used
