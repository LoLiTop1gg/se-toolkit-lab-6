# Agent

## Overview

A CLI agent that answers questions using an LLM.

## LLM Provider

Qwen Code API deployed on VM. Model: qwen3-coder-plus.

## How to run

```bash
uv run agent.py "What does REST stand for?"
```

## Output

```json
{"answer": "Representational State Transfer.", "tool_calls": []}
```

## Architecture

- Reads LLM_API_KEY, LLM_API_BASE, LLM_MODEL from .env.agent.secret
- Takes question from CLI argument
- Sends to LLM via OpenAI-compatible API
- Prints JSON with answer and tool_calls to stdout
- All debug output goes to stderr
