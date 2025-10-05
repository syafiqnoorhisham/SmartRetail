from django.conf import settings
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)


def get_supabase_client() -> Client:
    """
    Initialize and return Supabase client with anon key (public operations)
    """
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY
    
    if not url or not key:
        raise ValueError("Supabase URL and Key must be set in environment variables")
    
    return create_client(url, key)


def get_supabase_admin_client() -> Client:
    """
    Initialize and return Supabase admin client with service role key
    This client can bypass RLS and perform admin operations like:
    - Creating users with pre-verified emails
    - Managing user accounts programmatically
    
    Returns None if service role key is not configured.
    """
    url = settings.SUPABASE_URL
    service_role_key = getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', None)
    
    if not url:
        raise ValueError("Supabase URL must be set in environment variables")
    
    if not service_role_key:
        logger.warning(
            "⚠️ SUPABASE_SERVICE_ROLE_KEY not configured. "
            "Admin operations will not be available. "
            "Users created via invitation will require email confirmation."
        )
        return None
    
    return create_client(url, service_role_key)
