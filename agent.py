import sys
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(".env.agent.secret")

api_key = os.getenv("LLM_API_KEY")
api_base = os.getenv("LLM_API_BASE")
model = os.getenv("LLM_MODEL")

client = OpenAI(api_key=api_key, base_url=api_base)

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the project repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path from project root.",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories at a given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative directory path from project root.",
                    }
                },
                "required": ["path"],
            },
        },
    },
]


def is_safe_path(path):
    abs_path = os.path.abspath(os.path.join(PROJECT_ROOT, path))
    return abs_path.startswith(PROJECT_ROOT)


def read_file(path):
    if not is_safe_path(path):
        return "Error: path traversal not allowed"
    full_path = os.path.join(PROJECT_ROOT, path)
    if not os.path.exists(full_path):
        return f"Error: file not found: {path}"
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()


def list_files(path):
    if not is_safe_path(path):
        return "Error: path traversal not allowed"
    full_path = os.path.join(PROJECT_ROOT, path)
    if not os.path.exists(full_path):
        return f"Error: directory not found: {path}"
    return "\n".join(os.listdir(full_path))


def execute_tool(name, args):
    if name == "read_file":
        return read_file(args["path"])
    elif name == "list_files":
        return list_files(args["path"])
    return "Error: unknown tool"


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No question provided"}))
        sys.exit(1)

    question = sys.argv[1]
    print("Sending question to LLM...", file=sys.stderr)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that answers questions about this project. "
                "Use list_files to discover wiki files, then read_file to find the answer. "
                "Always include the source as a file path and section anchor, e.g. wiki/git-workflow.md#resolving-merge-conflicts. "
                'Return your final answer as JSON: {"answer": "...", "source": "..."}'
            ),
        },
        {"role": "user", "content": question},
    ]

    tool_calls_log = []
    max_tool_calls = 10
    tool_call_count = 0
    answer = ""
    source = ""

    while tool_call_count < max_tool_calls:
        response = client.chat.completions.create(
            model=model, messages=messages, tools=TOOLS, tool_choice="auto"
        )

        msg = response.choices[0].message

        if msg.tool_calls:
            messages.append(msg)
            for tc in msg.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments)
                print(f"Tool call: {name}({args})", file=sys.stderr)
                result = execute_tool(name, args)
                tool_calls_log.append(
                    {"tool": name, "args": args, "result": result[:500]}
                )
                messages.append(
                    {"role": "tool", "tool_call_id": tc.id, "content": result}
                )
                tool_call_count += 1
        else:
            raw = msg.content or ""
            try:
                parsed = json.loads(raw)
                answer = parsed.get("answer", raw)
                source = parsed.get("source", "")
            except json.JSONDecodeError:
                answer = raw
                source = ""
            break

    print(
        json.dumps({"answer": answer, "source": source, "tool_calls": tool_calls_log})
    )


if __name__ == "__main__":
    main()
