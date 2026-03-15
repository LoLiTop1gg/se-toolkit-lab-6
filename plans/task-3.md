# Task 3 Plan

## New tool: query_api
- Parameters: method, path, body (optional)
- Authenticates with LMS_API_KEY from environment
- Returns JSON with status_code and body
- Base URL from AGENT_API_BASE_URL (default: http://localhost:42002)

## Environment variables
- LLM_API_KEY, LLM_API_BASE, LLM_MODEL from .env.agent.secret
- LMS_API_KEY from .env.docker.secret
- AGENT_API_BASE_URL optional, defaults to http://localhost:42002

## System prompt update
- Use query_api for data questions (counts, status codes, API errors)
- Use read_file/list_files for wiki and source code questions
