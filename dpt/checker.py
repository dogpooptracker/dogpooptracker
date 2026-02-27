"""Dog Poop Tracker - Health Check Engine.

Checks endpoints and classifies results into poop metrics.
Solid = fast + healthy. Liquid = down. You get the idea.
"""

import json
import time

import httpx


def classify_check(status_code, latency_ms, expected_status, timeout_ms, error=None):
    """Classify a health check result into poop consistency."""
    # Consistency based on health
    if error or status_code is None:
        consistency = "liquid"
    elif status_code != expected_status:
        if 500 <= (status_code or 0) < 600:
            consistency = "liquid"
        else:
            consistency = "soft"
    elif latency_ms and latency_ms > timeout_ms * 0.8:
        consistency = "soft"
    elif latency_ms and latency_ms > timeout_ms * 0.5:
        consistency = "normal"
    else:
        consistency = "solid"

    healthy = consistency in ("solid", "normal")
    return consistency, healthy


def check_endpoint(url, method="GET", headers=None, expected_status=200, timeout=10.0):
    """Run a health check against a single endpoint."""
    parsed_headers = headers if isinstance(headers, dict) else json.loads(headers or "{}")

    error = None
    status_code = None
    latency_ms = None
    response_size = None

    start = time.monotonic()
    try:
        with httpx.Client(timeout=timeout, follow_redirects=False) as client:
            response = client.request(method, url, headers=parsed_headers)
            latency_ms = round((time.monotonic() - start) * 1000, 1)
            status_code = response.status_code
            try:
                response_size = len(response.content)
            except Exception:
                response_size = None
    except httpx.TimeoutException:
        latency_ms = round(timeout * 1000, 1)
        error = "Request timed out"
    except httpx.ConnectError as e:
        latency_ms = round((time.monotonic() - start) * 1000, 1)
        error = f"Connection failed: {str(e)[:100]}"
    except Exception as e:
        latency_ms = round((time.monotonic() - start) * 1000, 1)
        error = f"Error: {str(e)[:100]}"

    consistency, healthy = classify_check(
        status_code, latency_ms, expected_status, timeout * 1000, error
    )

    return {
        "status_code": status_code,
        "latency_ms": latency_ms,
        "response_size": response_size,
        "consistency": consistency,
        "healthy": healthy,
        "error": error,
    }


def check_dog(dog):
    """Run health check for a dog (service) dict from the database."""
    result = check_endpoint(
        url=dog["url"],
        method=dog.get("method", "GET"),
        headers=dog.get("headers", "{}"),
        expected_status=dog.get("expected_status", 200),
        timeout=dog.get("timeout", 10.0),
    )
    result["dog_name"] = dog["name"]
    return result
