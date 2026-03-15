# Agent

## Overview

A CLI agent that answers questions using an LLM with tools.

## LLM Provider

Qwen Code API deployed on VM. Model: qwen3-coder-plus.

## How to run

```bash
uv run agent.py "How do you resolve a merge conflict?"
```

## Output

```json
{"answer": "...", "source": "wiki/git-workflow.md#...", "tool_calls": [...]}
```

## Tools

- **read_file** — reads file contents by relative path
- **list_files** — lists directory contents by relative path
- Both tools block path traversal (../)

## Agentic loop

1. Send question + tool definitions to LLM
2. If LLM returns tool_calls -> execute tools, feed results back
3. Repeat up to 10 times
4. When LLM returns text answer -> output JSON and exit
