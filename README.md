# AI for Programmers

This workspace contains the weekly exercises for the course.

## Setup with uv

```bash
cd /workspaces/AI_for_programmers
uv venv .venv
source .venv/bin/activate
uv sync
```

## Run the embedding example

```bash
cd /workspaces/AI_for_programmers
source .venv/bin/activate
export OPENAI_API_KEY="your_key_here"
python wk3/embedding/main.py
```

You can also use:

```bash
uv run python wk3/embedding/main.py
```
