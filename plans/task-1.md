# Task 1 Plan

## LLM Provider
Qwen Code API deployed on VM. Model: qwen3-coder-plus.
API base: http://10.93.24.227:42005/v1

## Structure
- Read LLM_API_KEY, LLM_API_BASE, LLM_MODEL from .env.agent.secret
- Take question from CLI argument
- Send to LLM via OpenAI-compatible API
- Print JSON with answer and tool_calls to stdout
