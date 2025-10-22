## String Analytics Service

This project exposes a FastAPI-powered backend that stores raw text values and serves precomputed analytics about them (length, unique characters, palindrome status, etc.). The service is intentionally lightweight and uses an in-memory store, making it ideal for workshops, hackathons, or interview exercises that focus on API design.

### Features
- Create a string resource and receive analytic metadata in one request.
- Fetch individual strings or list them with fine-grained filters.
- Translate simple natural-language queries into API filters.
- Delete strings that are no longer needed.

### Requirements
- Python 3.10+

Install project dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running Locally
1. **Activate your environment** (skip if already active):
   ```bash
   source .venv/bin/activate
   ```
2. **Start the ASGI server** (defaults to `http://127.0.0.1:8000`):
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
   > Adjust the module path if your FastAPI `FastAPI()` instance lives outside `main.py`.

3. **Populate the store** *(optional)*: use the POST endpoint below to seed data after each restart—the in-memory store resets on shutdown.

### API Reference

All endpoints are rooted at `/strings`.

#### 1. Create / Analyze String
- **POST** `/strings`
- **Payload**
  ```json
  {
    "value": "string to analyze"
  }
  ```
- **Responses**
  - `201 Created`: Returns the full `StringResource`.
  - `400 Bad Request`: Missing `value` key.
  - `409 Conflict`: Value already stored.
  - `422 Unprocessable Entity`: `value` is not a string.

Example:
```bash
curl -X POST http://localhost:8000/strings \
  -H "Content-Type: application/json" \
  -d '{"value": "level"}'
```

#### 2. Get Specific String
- **GET** `/strings/{string_value}`
- **Responses**
  - `200 OK`: Returns the stored resource.
  - `404 Not Found`: Value does not exist.

Example:
```bash
curl http://localhost:8000/strings/level
```

#### 3. Get All Strings with Filtering
- **GET** `/strings`
- **Query Parameters**
  - `is_palindrome` (bool)
  - `min_length` (int)
  - `max_length` (int)
  - `word_count` (int)
  - `contains_character` (single character)
- **Responses**
  - `200 OK`: Returns a collection envelope with `data`, `count`, and `filters_applied`.
  - `400 Bad Request`: Invalid query parameter types or conflicting ranges.

Example:
```bash
curl "http://localhost:8000/strings?is_palindrome=true&min_length=5"
```

#### 4. Natural Language Filtering
- **GET** `/strings/filter-by-natural-language?query=...`
- **Responses**
  - `200 OK`: `data`, `count`, and `interpreted_query`.
  - `400 Bad Request`: Query could not be parsed.
  - `422 Unprocessable Entity`: Conflicting filters inferred.

Example:
```bash
curl "http://localhost:8000/strings/filter-by-natural-language?query=all%20single%20word%20palindromic%20strings"
```

#### 5. Delete String
- **DELETE** `/strings/{string_value}`
- **Responses**
  - `204 No Content`: Resource removed.
  - `404 Not Found`: Value does not exist.

Example:
```bash
curl -X DELETE http://localhost:8000/strings/level
```

### Data Models

| Field | Description |
| --- | --- |
| `StringResource.id` | SHA-256 hex digest of the string. |
| `StringResource.value` | Original string value. |
| `StringResource.created_at` | Timestamp when the resource was created. |
| `StringProperties.length` | Character count (including whitespace). |
| `StringProperties.is_palindrome` | Case-insensitive palindrome flag. |
| `StringProperties.unique_characters` | Number of distinct characters. |
| `StringProperties.word_count` | Number of whitespace-delimited words. |
| `StringProperties.sha256_hash` | SHA-256 hex digest (duplicate of `id`). |
| `StringProperties.character_frequency_map` | Count per character. |

### Extra Notes
- **Persistence**: The project currently relies on an in-memory dictionary. Restarting the server clears all data. Swap `_STRING_STORE` with a database or cache layer if durability is required.
- **Validation**: Pydantic models are the source of truth for response shapes and filter constraints.
- **Schema Generation**: FastAPI automatically serves OpenAPI docs at `/docs` (Swagger UI) and `/redoc`.
- **Testing**: Consider adding unit tests around `mw.py` and request/response tests using `TestClient` to guard against regressions.
- **Virtual Environments**: Recommended to avoid polluting global Python installations.

