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


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No question provided"}))
        sys.exit(1)

    question = sys.argv[1]
    print(f"Sending question to LLM...", file=sys.stderr)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant. Answer concisely.",
            },
            {"role": "user", "content": question},
        ],
    )

    answer = response.choices[0].message.content
    print(json.dumps({"answer": answer, "tool_calls": []}))


if __name__ == "__main__":
    main()
