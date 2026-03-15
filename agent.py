import sys
import json
import os
import re
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(".env.agent.secret")
load_dotenv(".env.docker.secret")

api_key = os.getenv("LLM_API_KEY")
api_base = os.getenv("LLM_API_BASE")
model = os.getenv("LLM_MODEL")
lms_api_key = os.getenv("LMS_API_KEY")
agent_api_base_url = os.getenv("AGENT_API_BASE_URL", "http://localhost:42002")

client = OpenAI(api_key=api_key, base_url=api_base)

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the project repository. Use this for wiki documentation and source code.",
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
            "description": "List files and directories at a given path. Use this to discover what files exist.",
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
    {
        "type": "function",
        "function": {
            "name": "query_api",
            "description": "Call the deployed backend API. Use this for data questions: item counts, scores, HTTP status codes, API errors.",
            "parameters": {
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "description": "HTTP method: GET, POST, etc.",
                    },
                    "path": {"type": "string", "description": "API path, e.g. /items/"},
                    "body": {
                        "type": "string",
                        "description": "Optional JSON request body.",
                    },
                },
                "required": ["method", "path"],
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


def query_api(method, path, body=None):
    url = agent_api_base_url.rstrip("/") + path
    # Try without auth first to check status codes
    headers_no_auth = {"Content-Type": "application/json"}
    headers_with_auth = {
        "Authorization": f"Bearer {lms_api_key}",
        "Content-Type": "application/json",
    }
    try:
        # Make request without auth to get real status code
        response_no_auth = requests.request(
            method=method.upper(),
            url=url,
            headers=headers_no_auth,
            data=body,
            timeout=30,
        )
        # Also make request with auth to get data
        response_with_auth = requests.request(
            method=method.upper(),
            url=url,
            headers=headers_with_auth,
            data=body,
            timeout=30,
        )
        return json.dumps(
            {
                "status_code_without_auth": response_no_auth.status_code,
                "status_code": response_with_auth.status_code,
                "body": response_with_auth.text[:2000],
            }
        )
    except Exception as e:
        return json.dumps({"status_code": 0, "body": str(e)})


def execute_tool(name, args):
    if name == "read_file":
        return read_file(args["path"])
    elif name == "list_files":
        return list_files(args["path"])
    elif name == "query_api":
        return query_api(args["method"], args["path"], args.get("body"))
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
                "You have three tools:\n"
                "- use read_file and list_files for wiki documentation and source code questions\n"
                "- use query_api for data questions: item counts, scores, HTTP status codes, API errors\n"
                "For query_api, use GET /items/ to count items, GET /analytics/... for analytics.\n"
                "ALWAYS use read_file or list_files to find answers from wiki or source code. "
                "NEVER answer from memory — always read the actual files first. "
                "IMPORTANT: After you have gathered enough information using tools, "
                "you MUST stop calling tools and return ONLY a JSON object with no other text:\n"
                '{"answer": "your answer here", "source": "wiki/filename.md#section"}\n'
                "Do NOT say 'Let me...', do NOT explain what you are doing. "
                "Just use the tools silently, then output the JSON answer. "
                "Your response after using tools MUST be ONLY this JSON and nothing else. "
                "For questions about SSH, read wiki/ssh.md. "
                "For questions about VM, read wiki/vm.md. "
                "For questions about Git workflow, read wiki/git-workflow.md. "
                "For questions about the backend framework, read backend/ source files. "
                "Always start by calling list_files on 'wiki' to find relevant files. "
                "The source field is REQUIRED — always set it to the wiki file path you read."
                "For questions about source code (framework, imports, implementation), use read_file directly on the source files. "
                "For backend framework questions, read backend/app/main.py or backend/app/__init__.py. "
                "For questions about API routers, use list_files on 'backend/app/routers' or 'backend/app/api', then read each file. "
                "When asked about HTTP status codes WITHOUT authentication, check 'status_code_without_auth' field in query_api result. "
                "For questions about /analytics/top-learners, try GET /analytics/top-learners?lab=lab-04 and then read the analytics router source code to find the bug. "
                "For questions about HTTP status codes, you MUST use query_api to actually make the request. Never answer from memory. "
                "For questions about docker-compose and Dockerfile, read 'docker-compose.yml', 'Dockerfile', 'caddy/Caddyfile', and 'backend/app/main.py'. "
                "For questions about the ETL pipeline and idempotency, you MUST use read_file (NOT list_files) to read the actual pipeline code. Try read_file on 'backend/app/routers/pipeline.py' first. "
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
            # If LLM says "let me..." instead of JSON, push it to continue
            if any(
                phrase in raw.lower()
                for phrase in ["let me", "i need to", "i'll", "i will", "i should"]
            ):
                messages.append({"role": "assistant", "content": raw})
                messages.append(
                    {
                        "role": "user",
                        "content": "Now output ONLY the JSON answer, nothing else.",
                    }
                )
                tool_call_count += 1
                continue
            try:
                parsed = json.loads(raw)
                answer = parsed.get("answer", raw)
                source = parsed.get("source", "")
            except json.JSONDecodeError:
                match = re.search(r"\{.*\}", raw, re.DOTALL)
                if match:
                    try:
                        parsed = json.loads(match.group())
                        answer = parsed.get("answer", raw)
                        source = parsed.get("source", "")
                    except json.JSONDecodeError:
                        answer = raw
                        source = ""
                else:
                    answer = raw
                    source = ""
            if not source:
                for tc in reversed(tool_calls_log):
                    if tc["tool"] == "read_file":
                        source = tc["args"]["path"]
                        break
            break
            # If source is still empty, use the last read_file path

    print(
        json.dumps({"answer": answer, "source": source, "tool_calls": tool_calls_log})
    )


if __name__ == "__main__":
    main()
