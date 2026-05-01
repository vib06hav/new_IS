##PROVIDER ROUTING

"""
Features
Provider Routing
AICredits automatically routes your requests to the best available upstream provider, with intelligent fallback, health checking, and round-robin load balancing across API keys.

Overview
Every request you send is dispatched through a routing pipeline that selects the right provider based on the model ID you specify. If the primary provider is degraded or unavailable, the request automatically fails over to an alternative route — all transparently, with no code changes needed.

This means you get the reliability of a multi-provider setup with the simplicity of a single API key and endpoint.

Model ID Format
The model ID you send in your request controls which provider handles it. AICredits supports two formats:

Explicit Routing
Use provider/model-name to target a specific provider directly:

Model ID	Provider
openai/gpt-5.4	OpenAI
openai/gpt-4o	OpenAI
openai/gpt-4o-mini	OpenAI
anthropic/claude-sonnet-4-20250514	Anthropic
anthropic/claude-haiku-4-5-20251001	Anthropic
google/gemini-2.0-flash	Google Gemini
deepseek/deepseek-chat	DeepSeek
mistral/mistral-large-latest	Mistral
x-ai/grok-beta	xAI
Heuristic Routing
You can also pass model names without a provider prefix. AICredits infers the provider from the model ID pattern:

Prefix Pattern	Routed To
gpt-*, o1-*, o3-*	OpenAI
claude-*	Anthropic
gemini-*	Google Gemini
deepseek-*	DeepSeek
mistral-*, mixtral-*	Mistral
grok-*	xAI
(unknown prefix)	Routed based on availability
Use Explicit IDs in Production
Explicit provider prefixes (e.g., openai/gpt-4o) are recommended in production so your routing intent is unambiguous and resilient to model name changes.

Fallback Chain
Requests are routed directly to the upstream provider. If the provider returns an error or is temporarily unavailable, the request is retried with exponential backoff across any remaining healthy keys for that provider.

1
Direct Provider
Calls the upstream provider directly using round-robin across your configured API keys. Each key is health-checked — unhealthy keys are skipped automatically.
2
Retry with Backoff
On 429 or 5xx responses, retries are attempted with exponential backoff (500ms → 1s → 2s, capped at 5s) across remaining healthy keys.
Info
For models where no direct provider key is configured, requests are routed through an aggregated provider pool as a fallback. Adding direct provider API keys is recommended for cost efficiency.

Circuit Breaker
AICredits tracks the health of each provider API key individually. When a key returns repeated failures, it is temporarily marked unhealthy and skipped:

Aspect	Behavior
Unhealthy threshold	Key is marked unhealthy on consecutive 5xx responses
Skip duration	Unhealthy keys are skipped for 30 seconds
Recovery	Key is automatically re-enabled after the skip window expires
Scope	Per API key, not per provider — other keys for the same provider still work
Round-Robin Key Selection
When multiple API keys are configured for a provider, requests are distributed evenly across healthy keys using round-robin selection. This spreads load and avoids rate limit exhaustion on a single key.

If a key is unhealthy (circuit open), it is automatically excluded from the rotation until it recovers.
"""

##STREAMING 

"""
Features
Streaming
Stream responses token-by-token using Server-Sent Events (SSE). AICredits normalises every provider's streaming format into the standard OpenAI SSE protocol, so all compatible SDKs and frameworks work without modification.

Overview
Set stream: true in any chat completions request to enable streaming. The response is a stream of server-sent events, each containing a delta (partial token). The stream ends with a final data: [DONE] event.

Streaming works across all supported providers — OpenAI, Anthropic, Google Gemini, DeepSeek, Mistral, and xAI. Each provider uses a different native streaming format, but AICredits translates all of them to the OpenAI SSE format your client expects.

Basic Streaming
Python
TypeScript
cURL
python
Copy
from openai import OpenAI

client = OpenAI(
    base_url="https://api.aicredits.in/v1",
    api_key="sk-your-key-here",
)

stream = client.chat.completions.create(
    model="openai/gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Write a poem about the Indian monsoon."},
    ],
    stream=True,
)

for chunk in stream:
    content = chunk.choices[0].delta.content
    if content is not None:
        print(content, end="", flush=True)

print()  # Newline after stream completes
Streaming with Tool Calls
Tool calls are fully supported in streaming mode. Tool call deltas arrive as incremental JSON fragments that the OpenAI SDK reassembles for you:

streaming_tools.py
Copy
from openai import OpenAI

client = OpenAI(
    base_url="https://api.aicredits.in/v1",
    api_key="sk-your-key-here",
)

tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather for a city",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"},
            },
            "required": ["city"],
        },
    },
}]

stream = client.chat.completions.create(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "What's the weather in Mumbai?"}],
    tools=tools,
    stream=True,
)

tool_call_chunks = []
for chunk in stream:
    delta = chunk.choices[0].delta
    if delta.content:
        print(delta.content, end="", flush=True)
    if delta.tool_calls:
        tool_call_chunks.extend(delta.tool_calls)
SSE Format
Each streamed event follows the OpenAI SSE format. Here is a sample of raw events you would receive:

Raw SSE Events
Copy
data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1709123456,"model":"gpt-4o-mini","choices":[{"index":0,"delta":{"role":"assistant","content":""},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1709123456,"model":"gpt-4o-mini","choices":[{"index":0,"delta":{"content":"The"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1709123456,"model":"gpt-4o-mini","choices":[{"index":0,"delta":{"content":" monsoon"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1709123456,"model":"gpt-4o-mini","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
Billing & Token Counting
Streaming requests are billed identically to non-streaming requests. Token counts and costs are calculated from the complete request and response:

Aspect	Behavior
Token counting	Prompt + completion tokens are counted from the full response
Cost calculation	Same formula as non-streaming: USD cost → INR via live forex rate
Deduction timing	Balance is deducted after the stream completes (not per-chunk)
Partial responses	If the client disconnects mid-stream, tokens already generated are still billed
Framework Integrations
AICredits streaming works out of the box with popular frameworks:

Vercel AI SDK
LangChain
typescript
Copy
import { createOpenAI } from "@ai-sdk/openai";
import { streamText } from "ai";

const aicredits = createOpenAI({
  baseURL: "https://api.aicredits.in/v1",
  apiKey: process.env.AICREDITS_API_KEY!,
});

// In a Next.js Route Handler (app/api/chat/route.ts):
export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: aicredits("openai/gpt-4o-mini"),
    messages,
  });

  return result.toDataStreamResponse();
}
Error Handling
Errors during streaming are delivered as a final SSE event before the stream closes. The OpenAI SDK surfaces these as exceptions:

stream_error_handling.py
Copy
from openai import OpenAI, APIStatusError, APIConnectionError

client = OpenAI(
    base_url="https://api.aicredits.in/v1",
    api_key="sk-your-key-here",
)

try:
    stream = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello"}],
        stream=True,
    )
    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            print(content, end="", flush=True)

except APIStatusError as e:
    if e.status_code == 402:
        print("\nInsufficient credits — top up your wallet.")
    elif e.status_code == 429:
        print("\nRate limit exceeded — slow down requests.")
    else:
        print(f"\nAPI error {e.status_code}: {e.message}")

except APIConnectionError:
    print("\nConnection error — check your network.")
Tip
See the Error Handling guide for the full list of error codes and retry strategies.
"""

##TOOL CALLING

"""
Tool Calling
Give models the ability to call your functions. AICredits supports the full OpenAI tool calling API — define tools, receive structured call arguments, execute them, and feed results back to the model.

Overview
Tool calling (also called function calling) allows you to define a set of functions that the model can choose to invoke. The model returns structured JSON arguments for the function it wants to call — you execute the function and feed the result back for a final response.

Because AICredits is OpenAI-compatible, you use the exact same tools parameter and tool_calls response format as the OpenAI API — across all supported models.

Defining Tools
Tools are defined as a JSON Schema object in the tools array:

Define tools
Copy
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "Get the current stock price for a given ticker symbol.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "The stock ticker symbol, e.g. RELIANCE, TCS, INFY",
                    },
                    "exchange": {
                        "type": "string",
                        "enum": ["NSE", "BSE"],
                        "description": "The stock exchange",
                    },
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_company_info",
            "description": "Get basic information about a listed company.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"},
                },
                "required": ["ticker"],
            },
        },
    },
]
Basic Tool Call
Python
TypeScript
python
Copy
import json
from openai import OpenAI

client = OpenAI(
    base_url="https://api.aicredits.in/v1",
    api_key="sk-your-key-here",
)

# Step 1: Send request with tools
response = client.chat.completions.create(
    model="openai/gpt-4o-mini",
    messages=[
        {"role": "user", "content": "What's the stock price of Reliance Industries?"}
    ],
    tools=tools,
    tool_choice="auto",
)

message = response.choices[0].message
print("Finish reason:", response.choices[0].finish_reason)
# → "tool_calls"

if message.tool_calls:
    tool_call = message.tool_calls[0]
    print("Tool:", tool_call.function.name)
    print("Args:", tool_call.function.arguments)
    # → {"ticker": "RELIANCE", "exchange": "NSE"}
Handling the Response
After executing the tool, send the result back to the model as a tool role message:

Full tool call loop
Copy
import json
from openai import OpenAI

client = OpenAI(
    base_url="https://api.aicredits.in/v1",
    api_key="sk-your-key-here",
)

messages = [
    {"role": "user", "content": "What's the stock price of Reliance Industries?"}
]

# Step 1: Initial request
response = client.chat.completions.create(
    model="openai/gpt-4o-mini",
    messages=messages,
    tools=tools,
)

assistant_message = response.choices[0].message
messages.append(assistant_message)  # Add assistant's tool call to history

# Step 2: Execute the tool
if assistant_message.tool_calls:
    for tool_call in assistant_message.tool_calls:
        args = json.loads(tool_call.function.arguments)

        # Your actual function execution
        if tool_call.function.name == "get_stock_price":
            result = {"price": 2847.50, "currency": "INR", "change": "+1.2%"}
        else:
            result = {"error": "Unknown function"}

        # Step 3: Add tool result to messages
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result),
        })

# Step 4: Get final response
final_response = client.chat.completions.create(
    model="openai/gpt-4o-mini",
    messages=messages,
    tools=tools,
)

print(final_response.choices[0].message.content)
# → "The current stock price of Reliance Industries (RELIANCE) is ₹2,847.50, up 1.2% today."
Parallel Tool Calls
Models can request multiple tool calls in a single response. AICredits passes these through unchanged — execute them in parallel for best performance:

Parallel tool calls
Copy
import asyncio
import json
from openai import AsyncOpenAI

client = AsyncOpenAI(
    base_url="https://api.aicredits.in/v1",
    api_key="sk-your-key-here",
)

async def execute_tool(tool_call):
    args = json.loads(tool_call.function.arguments)
    if tool_call.function.name == "get_stock_price":
        # Simulate API call
        return {"ticker": args["ticker"], "price": 1234.56}
    return {}

async def main():
    messages = [{"role": "user", "content": "Compare prices of TCS and Infosys"}]

    response = await client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=messages,
        tools=tools,
    )

    tool_calls = response.choices[0].message.tool_calls
    messages.append(response.choices[0].message)

    # Execute all tool calls in parallel
    results = await asyncio.gather(*[execute_tool(tc) for tc in tool_calls])

    for tool_call, result in zip(tool_calls, results):
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result),
        })

    final = await client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=messages,
    )
    print(final.choices[0].message.content)

asyncio.run(main())
Tool Choice
Control which tools the model can use with the tool_choice parameter:

Value	Behavior
"auto"	Model decides whether to call a tool (default)
"none"	Model will not call any tool
"required"	Model must call at least one tool
{"type": "function", "function": {"name": "my_fn"}}	Force a specific tool to be called
Provider Support
Tool calling is supported across all major models. For providers that use a different native format (e.g., Anthropic's tool use), AICredits translates the request and response automatically:

Provider	Models	Tool Calling
OpenAI	GPT-5.4, GPT-4o, GPT-4o-mini, o1, o3	Full support
Anthropic	Claude Sonnet, Claude Haiku	Full support
Google	Gemini 2.0 Flash, Gemini 1.5 Pro	Full support
DeepSeek	DeepSeek Chat, DeepSeek R1	Full support
Mistral	Mistral Large, Mistral Small	Full support
xAI	Grok Beta	Full support
Info
The OpenAI SDK handles response parsing for you. Regardless of which provider serves the request, message.tool_calls will always be in the OpenAI format.
"""

STRUCTURED OUTPUT

"""
Features
Structured Outputs
Reliably extract structured data from any model. Use JSON mode for basic JSON output, or strict schema validation for guaranteed structure. AICredits also includes automatic response healing to fix malformed JSON from providers.

Overview
There are two ways to get structured output from a model:

Method	How	Best For
JSON Mode	response_format: {type: "json_object"}	Any valid JSON — you define the schema in the prompt
Structured Outputs	response_format: {type: "json_schema", ...}	Strict adherence to a defined JSON Schema (OpenAI models)
JSON Mode
Set response_format: { "type": "json_object" } to instruct the model to return valid JSON. You must also describe the desired JSON structure in your system or user prompt.

Always describe the schema in your prompt
JSON mode guarantees the output is parseable JSON, but does not guarantee the keys or structure. Always tell the model exactly what JSON shape you want in the prompt.

Python
TypeScript
python
Copy
import json
from openai import OpenAI

client = OpenAI(
    base_url="https://api.aicredits.in/v1",
    api_key="sk-your-key-here",
)

response = client.chat.completions.create(
    model="openai/gpt-4o-mini",
    response_format={"type": "json_object"},
    messages=[
        {
            "role": "system",
            "content": """Extract invoice data and return JSON with these fields:
{
  "vendor": string,
  "amount": number,
  "currency": string,
  "date": string (YYYY-MM-DD),
  "items": [{"description": string, "quantity": number, "price": number}]
}""",
        },
        {
            "role": "user",
            "content": "Invoice from TechCorp dated 15 Jan 2025 for 3x server licenses at ₹4500 each.",
        },
    ],
)

data = json.loads(response.choices[0].message.content)
print(data["vendor"])  # TechCorp
print(data["amount"])  # 13500
Structured Outputs (JSON Schema)
For strict schema enforcement, use structured outputs with a full JSON Schema definition. The model will only output JSON that matches the schema exactly (supported on OpenAI GPT-4o and later models):

structured_outputs.py
Copy
from openai import OpenAI
import json

client = OpenAI(
    base_url="https://api.aicredits.in/v1",
    api_key="sk-your-key-here",
)

response = client.chat.completions.create(
    model="openai/gpt-4o-mini",
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "invoice",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "vendor": {"type": "string"},
                    "amount": {"type": "number"},
                    "currency": {"type": "string", "enum": ["INR", "USD", "EUR"]},
                    "date": {"type": "string", "description": "ISO 8601 date"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "quantity": {"type": "integer"},
                                "unit_price": {"type": "number"},
                            },
                            "required": ["description", "quantity", "unit_price"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["vendor", "amount", "currency", "date", "items"],
                "additionalProperties": False,
            },
        },
    },
    messages=[
        {"role": "user", "content": "Parse: TechCorp invoice, 3x server licenses at ₹4500 each, 15 Jan 2025"},
    ],
)

invoice = json.loads(response.choices[0].message.content)
print(invoice)
Response Healing
When JSON mode is enabled and a provider returns malformed JSON, AICredits automatically attempts to repair the response before returning it to you. This handles common issues:

Truncated JSON (missing closing brackets or braces)
Markdown code fences wrapping the JSON (```json ... ```)
Extra text or commentary before or after the JSON object
Trailing commas and other minor syntax errors
Response healing example
Copy
# Provider returned this (truncated):
'{"vendor": "TechCorp", "amount": 13500, "items": [{"description": "Server'

# AICredits response healing produces:
'{"vendor": "TechCorp", "amount": 13500, "items": [{"description": "Server"}]}'
Info
Response healing is transparent — you receive valid JSON even when the provider's raw output was slightly malformed. When healing is not possible, the raw response is returned and you will need to handle the parsing error in your code.

Prompting Tips
These practices lead to the most reliable structured output:

Show an example in the system prompt
Include a sample JSON object in your system prompt so the model has a concrete target format.
Use snake_case keys
Models handle snake_case consistently across languages and are less likely to hallucinate alternate casings.
Enumerate allowed values
For fields with a fixed set of values, list them explicitly: "status must be one of: pending, approved, rejected".
Set temperature to 0 for extraction tasks
Deterministic extraction (temperature: 0) reduces hallucinated field values when the answer is in the input.
Provider Support
Provider	JSON Mode	Strict JSON Schema
OpenAI GPT-4o / GPT-4o-mini	Yes	Yes
OpenAI o1, o3	Yes	Yes
Anthropic Claude	Yes (via prompt)	Via tool calling
Google Gemini	Yes	Partial
DeepSeek	Yes	No
Mistral	Yes	No
Tip
For maximum portability, use JSON mode with a clear prompt schema. Strict JSON Schema mode is most reliable on OpenAI models; for other providers, combine JSON mode with precise system prompt instructions.
"""

##SEMANTIC CACHING

"""
Features
Semantic Caching
AICredits caches LLM responses based on the semantic meaning of your queries. When a new request is semantically similar to a previous one, the cached response is returned instantly — saving cost and reducing latency.

Overview
Traditional caching matches exact strings — the query must be byte-for-byte identical to get a cache hit. Semantic caching uses vector embeddings to understand what you are asking, so similar questions hit the same cache entry even when phrased differently.

CACHE HIT
Query 1: "What is the capital of India?"
Query 2: "Which city is the capital of India?" — same meaning, returns cached response
CACHE MISS
Query 3: "What is the largest city in India?" — different meaning, calls provider
Optional Feature
Semantic caching is opt-in and disabled by default. Contact your administrator to enable it for your account. When disabled, all requests pass through to providers with no caching overhead.

How It Works
The caching pipeline runs on every request:

1
Embed the query
The incoming message content is converted into a vector embedding using a fast embedding model.
2
Similarity search
The embedding is compared against your cache using pgvector cosine similarity. This lookup is a single indexed database query.
3
Cache hit (≥95% similarity)
If a match is found above the similarity threshold, the cached response is returned immediately. No provider call is made. The response is marked with X-Cache-Status: HIT.
4
Cache miss (<95% similarity)
The request is forwarded to the provider normally. Once the response arrives, it is stored in your cache for future use.
Parameter	Value
Similarity algorithm	Cosine similarity (pgvector)
Hit threshold	95% cosine similarity
Storage	PostgreSQL with pgvector extension
Cache TTL	30 days from last write
Cache Hit Detection
Cache hits are transparent — your application receives a valid response in the same format regardless of whether it was served from cache or the upstream provider. Cached responses are typically returned significantly faster since no provider round-trip is required.

Scope & Privacy
Each user's cache is completely isolated:

Cache entries are scoped to your user account (your API key)
Other users cannot read from or write to your cache
Different API keys under the same account share the same cache
Cached responses are subject to your data retention policy
Privacy
If you are sending sensitive or user-specific queries that should never be cached (e.g., queries containing personally identifiable information), consider using the Metadata Only retention policy, which also disables caching for your account.

TTL & Expiration
Cache entries expire automatically after 30 days. There is no manual cache invalidation — entries are cleaned up by a background retention worker.

Info
If your underlying data changes and you need a fresh response, the simplest approach is to rephrase the query slightly (e.g., add today's date). Because the embedding will differ, it will fall below the similarity threshold and bypass the cache.

When to Use Caching
Semantic caching is most effective for applications with:

FAQ bots
Users ask the same support questions in many different ways — high cache hit rate
Knowledge base Q&A
Questions about a fixed corpus of documents reuse answers frequently
Classification pipelines
Repeated categorisation of similar inputs benefits heavily from caching
Development & testing
Running the same prompts repeatedly during testing incurs zero cost on hits
Limitations
Not suitable for real-time data
Cache hits return old responses. Do not use caching for queries where the answer changes (stock prices, current news).
Multi-turn conversations
Only the latest user message is embedded. For multi-turn chats, the full conversation context is not part of the similarity check.
Streaming
Cache hits do not use streaming — the full response is returned at once even if stream: true was requested.
"""

##GUARDRAILS

"""Guardrails
Configurable safety layers that process requests before they reach LLM providers. Guardrails include PII masking, keyword blocking, and automatic JSON response healing — all transparent to your application code.

Overview
Guardrails run inline on every request and response in the proxy pipeline:

Request → Provider
PII masking (redacts sensitive data before forwarding)
Keyword blocking (rejects requests containing blocked terms)
Provider → Response
Response healing (repairs malformed JSON when json_object mode is requested)
Optional Features
All guardrails are opt-in and disabled by default. When disabled, requests pass through unmodified with zero processing overhead. Contact your administrator to enable specific guardrails for your account or deployment.

PII Masking
When enabled, personally identifiable information is automatically detected and redacted from request content before it is forwarded to the LLM provider. The original content is never sent upstream — only the masked version.

This is useful for applications that process user-submitted text (forms, support tickets, documents) where you want to prevent PII from entering external AI systems.

PII masking example
Copy
# Original request content (what your application sends):
"My name is Priya Sharma, contact me at priya@example.com or +91-98765-43210.
My Aadhaar number is 1234 5678 9012."

# After PII masking (what is forwarded to the provider):
"My name is [NAME_REDACTED], contact me at [EMAIL_REDACTED] or [PHONE_REDACTED].
My Aadhaar number is [ID_REDACTED]."
Masking is one-way
PII masking modifies the request before it reaches the model. The model's response will reference the masked values (e.g., "[EMAIL_REDACTED]"), not the originals. Design your prompts accordingly — for example, avoid asking the model to "reply to the user's email address" when masking is enabled.

Detected PII Patterns
PII Type	Example	Masked As
Email address	user@example.com	[EMAIL_REDACTED]
Phone number	+91-98765-43210	[PHONE_REDACTED]
Indian mobile	9876543210	[PHONE_REDACTED]
Aadhaar number	1234 5678 9012	[ID_REDACTED]
PAN card	ABCDE1234F	[ID_REDACTED]
Credit card	4111 1111 1111 1111	[CARD_REDACTED]
Person names (heuristic)	Priya Sharma	[NAME_REDACTED]
Blocked Keywords
Administrators can configure a list of blocked keywords or phrases. Any request whose message content contains a blocked term is immediately rejected before reaching the provider — no tokens are consumed and no cost is incurred.

Blocked keyword response
Copy
# Response when a blocked keyword is detected:
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": {
    "message": "Request contains blocked content",
    "type": "guardrail_violation",
    "code": "blocked_keyword"
  }
}
The blocked keyword list is configured at the platform level by your administrator. Common use cases include:

Preventing competitor brand names in customer-facing applications
Blocking legally sensitive terms in regulated industries
Filtering out profanity or harmful content categories
Enforcing product naming conventions
Response Healing
When you request JSON output (response_format: { "type": "json_object" }) and the provider returns malformed JSON, AICredits automatically attempts to repair the response before returning it to your application.

Healing handles:

Truncated JSON (missing closing brackets or braces)
Markdown code fences (```json ... ```) wrapping the JSON
Extra text or commentary before or after the JSON object
Trailing commas after the last property
Single-quoted strings instead of double-quoted
Response healing example
Copy
# Provider returned (truncated + wrapped in markdown):
```json
{"vendor": "TechCorp", "amount": 13500, "items": [{"desc"

# After response healing:
{"vendor": "TechCorp", "amount": 13500, "items": [{"desc": ""}]}
Info
Response healing is a best-effort repair. If the response is too malformed to recover, the raw provider output is returned unchanged and your application will receive a JSON parse error. Always handle json.JSONDecodeError /JSON.parse errors in production code.

Guardrail Errors
Guardrail violations return a 400 Bad Request with a structured error body:

Error Code	Cause
blocked_keyword	Request content contains a configured blocked keyword
guardrail_violation	General guardrail rejection (content policy)
Privacy & Compliance
Guardrails complement your data retention policy for privacy compliance:

Setting	Effect
PII Masking ON	PII is stripped from the request before it reaches any external system, including logs
Retention: Metadata Only	Request and response content are not stored in AICredits logs — only token counts and costs
Both combined	Maximum privacy: PII never leaves your infra, and no content is stored server-side
Tip
For healthcare, fintech, or other regulated use cases, combine PII masking with the Metadata Only retention policy and contact your administrator to enable both settings.
"""