# Agent Harness

Agent Harness is a small Python adapter for running the same tool registry through
OpenAI Agents SDK or Anthropic Claude Agent SDK provider implementations. The core package
has no runtime SDK dependency; provider SDKs are imported lazily only when that provider is
used.

[![CI](https://github.com/evalops/agent-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/evalops/agent-harness/actions/workflows/ci.yml)
[![Bazel RBE](https://github.com/evalops/agent-harness/actions/workflows/bazel-rbe.yml/badge.svg)](https://github.com/evalops/agent-harness/actions/workflows/bazel-rbe.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## What It Provides

- A thread-safe global tool registry via `@register_tool`.
- JSON Schema generation from Python type hints, including `Optional`, `T | None`,
  `list[T]`, `dict`, `Literal`, and multi-type unions.
- A common `HarnessConfig` and `AgentResponse` shape across providers.
- Lazy OpenAI and Claude provider adapters.
- Provider comparison helpers for running the same prompt against multiple adapters.
- A built-in optional You.com search tool adapter.

The registry and schema generation work without OpenAI or Anthropic packages installed.
Actual model runs require the provider extras and API credentials.

## Install

```bash
pip install -e .
pip install -e ".[openai]"
pip install -e ".[anthropic]"
pip install -e ".[all]"
pip install -e ".[dev]"
```

Provider credentials:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Quick Start

```python
import asyncio

from agent_harness import AgentHarness, HarnessConfig, register_tool


@register_tool(description="Get weather for a city")
def get_weather(city: str) -> str:
    return f"Weather in {city}: sunny, 72F"


async def main() -> None:
    config = HarnessConfig(
        system_prompt="You are a helpful assistant.",
        tool_names=["get_weather"],
        max_turns=5,
        timeout_sec=30.0,
    )

    async with AgentHarness(provider="openai", config=config) as harness:
        response = await harness.run("What is the weather in Tokyo?")
        print(response.final_output)

        await harness.switch_provider("claude")
        response = await harness.run("What is the weather in Tokyo?")
        print(response.final_output)


asyncio.run(main())
```

## Tool Registry

Register a tool once and let each provider adapter wrap it for its SDK:

```python
from typing import Literal

from agent_harness import get_registry, register_tool


@register_tool(description="Score a deployment risk")
def score_risk(service: str, mode: Literal["fast", "safe"], retries: int | None = None) -> str:
    return f"{service}: {mode}, retries={retries}"


tool = get_registry().get("score_risk")
print(tool.json_schema)
```

Default values are not required in the generated schema. Parameters without annotations are
treated as strings.

## Configuration

```python
from agent_harness import HarnessConfig

config = HarnessConfig(
    system_prompt="You are an expert operator.",
    model="gpt-4o",
    max_turns=10,
    temperature=0.7,
    timeout_sec=30.0,
    max_output_tokens=1000,
    top_p=0.9,
    stop_sequences=["STOP"],
    tool_names=["score_risk"],
    retry_attempts=3,
    retry_backoff=1.0,
    request_id="optional-stable-id",
    provider_options={"permission_mode": "acceptEdits"},
)
```

Validation rejects non-positive turns, timeout, retry backoff, and output token limits;
temperatures outside `0.0..2.0`; `top_p` outside `0.0..1.0`; and negative retry counts.

## Optional You.com Search Tool

```python
import os

from agent_harness import HarnessConfig, register_you_com_search_tool

os.environ["YDC_API_KEY"] = "your_ydc_api_key"
register_you_com_search_tool(name="you_search")

config = HarnessConfig(
    system_prompt="Use web search when fresh context matters.",
    tool_names=["you_search"],
)
```

The adapter is intentionally non-fatal:

- Missing API key returns a setup message to the agent.
- HTTP or JSON failures return a concise error string.
- Empty result sets return `No web results found.`

## Provider Notes

OpenAI provider:

- Installs through `.[openai]`.
- Lazily imports `agents`.
- Wraps registered tools with `function_tool`.
- Runs through `Runner.run()` and streams through `Runner.run_streamed()`.

Claude provider:

- Installs through `.[anthropic]`.
- Lazily imports `claude_agent_sdk`.
- Exposes registered tools through an in-process MCP server.
- Accepts Claude-specific options through `provider_options`.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python3 -m pytest -q
make bazel-check
```

Remote execution smoke:

```bash
make bazel-rbe-smoke
```

The `Bazel RBE` GitHub Actions workflow runs on the EvalOps `bazel-rbe-dev` farm when
`BAZEL_RBE_ENABLED=true` is set for the repository. It uses the
`evalops-agent-harness-rbe` and `bazel-rbe` self-hosted labels.

## Repository Layout

```text
agent_harness.py          core registry, config, provider adapters
tests/                    pytest coverage
example_usage.py          provider examples
BUILD.bazel               Bazel pytest target
MODULE.bazel              Bazel module dependencies
```
