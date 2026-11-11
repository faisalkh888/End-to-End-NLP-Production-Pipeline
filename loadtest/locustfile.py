import os

from locust import HttpUser, task, between


WAIT_MIN_SECONDS = float(os.getenv("ATLAS_LOAD_WAIT_MIN", "0.2"))
WAIT_MAX_SECONDS = float(os.getenv("ATLAS_LOAD_WAIT_MAX", "1.0"))


class SupportAIUser(HttpUser):
    wait_time = between(WAIT_MIN_SECONDS, WAIT_MAX_SECONDS)

    @task(3)
    def qa(self):
        self.client.post("/v1/qa", json={"question": "How do I set up the API?", "access_level": "public"})

    @task(2)
    def triage(self):
        with self.client.post(
            "/v1/triage",
            json={"ticket": "Our API fails after deployment with an error"},
            name="/v1/triage",
            catch_response=True,
        ) as response:
            mode = response.headers.get("X-Triage-Mode", "unknown")
            if response.status_code >= 400:
                response.failure(f"HTTP {response.status_code}")
            elif mode.startswith("fallback-"):
                response.request_meta["name"] = f"/v1/triage ({mode})"
