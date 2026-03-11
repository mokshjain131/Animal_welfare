"""Supabase client — lazy singleton for the Supabase Python SDK."""

from supabase import create_client, Client

# ── Lazy singleton ───────────────────────────────────────────────────
_client: Client | None = None


def get_supabase() -> Client:
    """Create (once) and return the Supabase client."""
    global _client
    if _client is None:
        from config.settings import settings
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _client

