"""
AI Adoption Tracker — Platform Data Fetchers
Abstract base class + concrete fetchers for OpenAI and Anthropic admin APIs.
To add a new platform: create a new Fetcher subclass + add config.yaml entry.
"""
from __future__ import annotations

import datetime
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import httpx
import yaml

_DIR = Path(__file__).resolve().parent
try:
    _CFG = yaml.safe_load((_DIR / "config.yaml").read_text())
except FileNotFoundError:
    _CFG = {"platforms": {}, "refresh_interval_hours": 6, "cache_db": "data/ai_adoption_cache.db"}


class PlatformFetcher(ABC):
    """Base class for AI platform data fetching."""

    def __init__(self, platform_key: str, config: dict):
        self.platform_key = platform_key
        self.config = config
        self.label = config.get("label", platform_key)
        self.base_url = config.get("base_url", "")
        self.api_key = os.environ.get(config.get("env_var", ""), "")

    def is_configured(self) -> bool:
        """True if the API key env var is set."""
        return bool(self.api_key)

    @abstractmethod
    def fetch_users(self) -> list[dict]:
        """Return list of {email, name, role?} dicts."""

    @abstractmethod
    def fetch_usage(self, start_date: str, end_date: str) -> list[dict]:
        """Return list of {email, date, message_count, tokens, model} dicts."""

    def test_connection(self) -> tuple[bool, str]:
        """Test API connectivity. Returns (success, message)."""
        if not self.is_configured():
            return False, f"Environment variable {self.config.get('env_var', '?')} not set"
        try:
            users = self.fetch_users()
            return True, f"Connected — {len(users)} users found"
        except Exception as e:
            return False, str(e)


class OpenAIFetcher(PlatformFetcher):
    """Fetch user and usage data from OpenAI Admin API."""

    def fetch_users(self) -> list[dict]:
        if not self.is_configured():
            return []
        users = []
        url = f"{self.base_url}/organization/users"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            with httpx.Client(timeout=30) as client:
                after = None
                while True:
                    params = {"limit": 100}
                    if after:
                        params["after"] = after
                    resp = client.get(url, headers=headers, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                    for member in data.get("data", []):
                        email = member.get("email", "")
                        if email:
                            users.append({
                                "email": email.lower(),
                                "name": member.get("name", email.split("@")[0]),
                                "role": member.get("role", "member"),
                            })
                    if not data.get("has_more"):
                        break
                    after = data.get("last_id")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"OpenAI API error: {e.response.status_code} {e.response.text[:200]}") from e
        except httpx.RequestError as e:
            raise RuntimeError(f"OpenAI connection error: {e}") from e
        return users

    def fetch_usage(self, start_date: str, end_date: str) -> list[dict]:
        if not self.is_configured():
            return []
        records = []
        url = f"{self.base_url}/organization/usage"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        # Convert dates to unix timestamps for the API
        start_ts = int(datetime.datetime.strptime(start_date, "%Y-%m-%d").timestamp())
        end_ts = int(datetime.datetime.strptime(end_date, "%Y-%m-%d").timestamp())
        try:
            with httpx.Client(timeout=60) as client:
                # Fetch completions usage bucketed by user
                params = {
                    "start_time": start_ts,
                    "end_time": end_ts,
                    "bucket_width": "1d",
                    "group_by": ["user_email", "model"],
                }
                resp = client.get(url + "/completions", headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
                for bucket in data.get("data", []):
                    for result in bucket.get("results", []):
                        email = result.get("user_email", "")
                        if not email:
                            continue
                        # Each bucket has a start_time
                        bucket_date = datetime.datetime.fromtimestamp(
                            bucket.get("start_time", start_ts)
                        ).strftime("%Y-%m-%d")
                        records.append({
                            "email": email.lower(),
                            "date": bucket_date,
                            "message_count": result.get("num_completions", 0)
                                             or result.get("num_requests", 0) or 1,
                            "tokens": (result.get("num_tokens", 0)
                                       or result.get("input_tokens", 0)
                                       + result.get("output_tokens", 0)),
                            "model": result.get("model", "unknown"),
                        })
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"OpenAI usage API error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise RuntimeError(f"OpenAI connection error: {e}") from e
        return records


class AnthropicFetcher(PlatformFetcher):
    """Fetch user and usage data from Anthropic Admin API."""

    def fetch_users(self) -> list[dict]:
        if not self.is_configured():
            return []
        users = []
        url = f"{self.base_url}/organizations/users"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        try:
            with httpx.Client(timeout=30) as client:
                after_id = None
                while True:
                    params = {"limit": 100}
                    if after_id:
                        params["after_id"] = after_id
                    resp = client.get(url, headers=headers, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                    for member in data.get("data", []):
                        email = member.get("email", "")
                        if email:
                            users.append({
                                "email": email.lower(),
                                "name": member.get("name", email.split("@")[0]),
                                "role": member.get("role", "member"),
                            })
                    if not data.get("has_more"):
                        break
                    after_id = data.get("last_id")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Anthropic API error: {e.response.status_code} {e.response.text[:200]}") from e
        except httpx.RequestError as e:
            raise RuntimeError(f"Anthropic connection error: {e}") from e
        return users

    def fetch_usage(self, start_date: str, end_date: str) -> list[dict]:
        if not self.is_configured():
            return []
        records = []
        url = f"{self.base_url}/organizations/usage"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        try:
            with httpx.Client(timeout=60) as client:
                params = {
                    "start_date": start_date,
                    "end_date": end_date,
                    "group_by": "user,model",
                }
                resp = client.get(url, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
                for entry in data.get("data", []):
                    email = entry.get("user_email", entry.get("email", ""))
                    if not email:
                        continue
                    records.append({
                        "email": email.lower(),
                        "date": entry.get("date", start_date),
                        "message_count": entry.get("num_requests", 0)
                                         or entry.get("message_count", 0) or 1,
                        "tokens": (entry.get("input_tokens", 0)
                                   + entry.get("output_tokens", 0)),
                        "model": entry.get("model", "unknown"),
                    })
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Anthropic usage API error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise RuntimeError(f"Anthropic connection error: {e}") from e
        return records


# ── Factory ──────────────────────────────────────────────────────────────────

_FETCHER_CLASSES = {
    "openai": OpenAIFetcher,
    "anthropic": AnthropicFetcher,
}


def get_fetcher(platform_key: str) -> Optional[PlatformFetcher]:
    """Get a fetcher instance for a platform key from config."""
    platforms = _CFG.get("platforms", {})
    if platform_key not in platforms:
        return None
    cls = _FETCHER_CLASSES.get(platform_key)
    if not cls:
        return None
    return cls(platform_key, platforms[platform_key])


def get_all_fetchers() -> list[PlatformFetcher]:
    """Get fetcher instances for all configured platforms."""
    fetchers = []
    for key in _CFG.get("platforms", {}):
        f = get_fetcher(key)
        if f:
            fetchers.append(f)
    return fetchers
