## Local AI Card Beautifier — Configuration

| Key               | Type   | Default                              | Description                              |
|-------------------|--------|--------------------------------------|------------------------------------------|
| `api_url`         | str    | `http://127.0.0.1:8082/v1/chat/completions` | Local LLM endpoint (OpenAI-compatible)   |
| `model`           | str    | `local-model`                        | Model identifier sent in the request     |
| `temperature`     | float  | `0.7`                                | LLM sampling temperature                 |
| `max_tokens`      | int    | `2048`                               | Maximum tokens in the response           |
| `timeout_seconds` | int    | `60`                                 | HTTP request timeout                     |
| `default_template`| str    | `Concept Card (Grid Layout)`         | Default formatting template selected     |
