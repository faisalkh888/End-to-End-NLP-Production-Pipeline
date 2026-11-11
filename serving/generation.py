import os
import httpx


async def generate(
    prompt: str,
    *,
    system: str = "",
    url: str | None = None,
    model: str | None = None,
    completion: bool = False,
) -> str | None:
    url = (url if url is not None else os.getenv("GENERATOR_URL", "")).rstrip("/")
    if not url:
        return None
    body = {"model": model or os.getenv("GENERATOR_MODEL", "local-model"), "temperature": 0,
            "max_tokens": 256}
    if completion:
        body["prompt"] = prompt
        endpoint = "completions"
    else:
        body["messages"] = (
            ([{"role": "system", "content": system}] if system else [])
            + [{"role": "user", "content": prompt}]
        )
        endpoint = "chat/completions"
    headers = {}
    if os.getenv("GENERATOR_API_KEY"):
        headers["Authorization"] = f"Bearer {os.environ['GENERATOR_API_KEY']}"
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(f"{url}/v1/{endpoint}", json=body, headers=headers)
        response.raise_for_status()
        choice = response.json()["choices"][0]
        return choice["text"] if completion else choice["message"]["content"]
