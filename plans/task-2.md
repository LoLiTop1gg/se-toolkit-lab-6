# Task 2 Plan

## Tools
- read_file: reads file contents by relative path
- list_files: lists directory contents by relative path
- Both tools block path traversal (../)

## Agentic loop
1. Send question + tool definitions to LLM
2. If LLM returns tool_calls -> execute tools, feed results back
3. Repeat up to 10 times
4. When LLM returns text answer -> output JSON and exit

## Output
JSON with answer, source, tool_calls fields
