"""
razorpay_oauth_service.py
─────────────────────────
Handles Razorpay Technology Partner OAuth:
  • Generates the OAuth authorization URL
  • Exchanges auth-code for linked-account key_id / key_secret
  • Creates Razorpay orders using the CLIENT'S own keys (workspace isolation)
  • Verifies payment signatures using per-workspace secret
  • Initiates refunds via the client's account
  • Verifies webhook authenticity per workspace

SECURITY:
  • linked_key_id and linked_key_secret are NEVER returned to the frontend
  • All Razorpay API calls are made server-side using the workspace's own credentials
"""

import os
import hmac
import hashlib
import secrets
import requests
import logging
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# ── Razorpay OAuth endpoints ──────────────────────────────────────────────────
RAZORPAY_OAUTH_URL    = 'https://auth.razorpay.com/authorize'
RAZORPAY_TOKEN_URL    = 'https://auth.razorpay.com/token'
RAZORPAY_API_BASE     = 'https://api.razorpay.com/v1'

# UWOConnect Technology-Partner credentials (set in .env)
PARTNER_CLIENT_ID     = os.getenv('RAZORPAY_CLIENT_ID', '')
PARTNER_CLIENT_SECRET = os.getenv('RAZORPAY_CLIENT_SECRET', '')
REDIRECT_URI          = os.getenv('RAZORPAY_REDIRECT_URI', 'http://localhost:8080/api/razorpay/callback')


class RazorpayOAuthService:
    """Service for per-workspace Razorpay OAuth operations."""

    @staticmethod
    def get_oauth_authorize_url(state: str) -> str:
        """
        Build the Razorpay OAuth authorization URL.
        Redirects client to Razorpay to authorize UWOConnect as a platform.
        """
        if not PARTNER_CLIENT_ID or PARTNER_CLIENT_ID.startswith('your_razorpay'):
            # Local Dev Mock Sandbox Flow!
            mock_url = f"{REDIRECT_URI}?code=mock_authorization_code_12345&state={state}"
            logger.info(f"[Razorpay OAuth] Mock Redirect Flow initiated for state={state}")
            return mock_url

        params = {
            'response_type': 'code',
            'client_id': PARTNER_CLIENT_ID,
            'redirect_uri': REDIRECT_URI,
            'scope': 'read_write',
            'state': state,
        }
        query = '&'.join(f"{k}={v}" for k, v in params.items())
        url = f"{RAZORPAY_OAUTH_URL}?{query}"
        logger.info(f"[Razorpay OAuth] Generated authorize URL for state={state}")
        return url

    @staticmethod
    def exchange_code_for_tokens(code: str) -> dict:
        """
        Exchange the OAuth authorization code for access_token and linked account credentials.
        Returns: { access_token, refresh_token, linked_key_id, linked_key_secret, razorpay_account_id }
        """
        # If credentials are placeholders or code is mock, use local developer credentials in testing
        if not PARTNER_CLIENT_ID or PARTNER_CLIENT_ID.startswith('your_razorpay') or code.startswith('mock_'):
            logger.info(f"[Razorpay OAuth] Mock Exchange Flow initiated. Using local test key credentials.")
            local_key_id = os.getenv('RAZORPAY_KEY_ID', 'rzp_test_TGv2xByWyhTGoM')
            local_key_secret = os.getenv('RAZORPAY_KEY_SECRET', 'PNbRUxPh9kOtnTUHxp3rbUbs')
            return {
                'access_token':          local_key_secret,  # in OAuth mode, access_token acts as API authentication password
                'refresh_token':         'mock_refresh_token_ref_xyz123',
                'token_type':            'Bearer',
                'linked_key_id':         local_key_id,
                'linked_key_secret':     local_key_secret,
                'razorpay_account_id':   'acc_mock_razorpay123',
                'expires_in':            86400,
            }

        payload = {
            'client_id': PARTNER_CLIENT_ID,
            'client_secret': PARTNER_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
        }

        try:
            res = requests.post(RAZORPAY_TOKEN_URL, json=payload, timeout=15)
            data = res.json()
        except Exception as e:
            logger.error(f"[Razorpay OAuth] Token exchange failed: {e}")
            raise ConnectionError(f"Failed to connect to Razorpay: {str(e)}")

        if res.status_code != 200:
            error_msg = data.get('error_description') or data.get('error') or 'Token exchange failed'
            logger.error(f"[Razorpay OAuth] Token exchange error: {res.status_code} — {data}")
            raise ValueError(error_msg)

        return {
            'access_token':          data.get('access_token'),
            'refresh_token':         data.get('refresh_token'),
            'token_type':            data.get('token_type', 'Bearer'),
            'linked_key_id':         data.get('razorpay_account_id') or data.get('public_token'),
            'linked_key_secret':     data.get('access_token'),
            'razorpay_account_id':   data.get('razorpay_account_id') or '',
            'expires_in':            data.get('expires_in'),
        }



    # ─── Order creation (workspace-isolated) ─────────────────────────────────

    @staticmethod
    def create_product_order(rzp_connection, amount_inr: float, receipt_id: str, notes: dict = None) -> dict:
        """
        Create a Razorpay order using the CLIENT's own credentials.
        NEVER uses UWOConnect's global Razorpay keys.
        """
        from api.models import RazorpayConnection  # local import to avoid circular

        if not rzp_connection or not rzp_connection.is_connected():
            raise ValueError("Razorpay is not connected for this workspace.")

        # Use workspace's own key_id + key_secret (access_token acts as secret in OAuth mode)
        key_id     = rzp_connection.linked_key_id
        key_secret = rzp_connection.linked_key_secret

        if not key_id or not key_secret:
            raise ValueError("Razorpay credentials missing for this workspace.")

        amount_paise = int(float(amount_inr) * 100)

        payload = {
            'amount':   amount_paise,
            'currency': 'INR',
            'receipt':  receipt_id,
            'notes':    notes or {'platform': 'UWOConnect'},
        }

        try:
            res = requests.post(
                f"{RAZORPAY_API_BASE}/orders",
                json=payload,
                auth=(key_id, key_secret),
                timeout=15,
            )
            data = res.json()
        except Exception as e:
            logger.error(f"[Razorpay] Order creation failed for account {rzp_connection.razorpay_account_id}: {e}")
            raise ConnectionError(f"Razorpay API error: {str(e)}")

        if res.status_code in [200, 201] and 'id' in data:
            logger.info(f"[Razorpay] Order created: {data['id']} for account {rzp_connection.razorpay_account_id}")
            return {
                'razorpay_order_id': data['id'],
                'key_id':            key_id,   # safe to return — it's the public key
                'amount':            data['amount'],
                'currency':          data['currency'],
                'account_id':        rzp_connection.razorpay_account_id,
            }
        else:
            err = data.get('error', {}).get('description', 'Order creation failed')
            logger.error(f"[Razorpay] Order error: {data}")
            raise ValueError(err)

    # ─── Signature verification (per workspace) ───────────────────────────────

    @staticmethod
    def verify_payment_signature(rzp_connection, order_id: str, payment_id: str, signature: str) -> bool:
        """
        Verify Razorpay payment signature using the workspace's own key_secret.
        """
        if not rzp_connection or not rzp_connection.linked_key_secret:
            logger.warning("[Razorpay] Cannot verify signature — no key_secret for workspace.")
            return False

        try:
            msg = f"{order_id}|{payment_id}".encode('utf-8')
            secret = rzp_connection.linked_key_secret.encode('utf-8')
            generated = hmac.new(secret, msg, hashlib.sha256).hexdigest()
            result = hmac.compare_digest(generated, signature or '')
            logger.info(f"[Razorpay] Signature verification: {'PASS' if result else 'FAIL'} for order {order_id}")
            return result
        except Exception as e:
            logger.error(f"[Razorpay] Signature verification error: {e}")
            return False

    # ─── Webhook verification ─────────────────────────────────────────────────

    @staticmethod
    def verify_webhook_signature(payload_bytes: bytes, signature: str, webhook_secret: str) -> bool:
        """
        Verify Razorpay webhook X-Razorpay-Signature header using workspace webhook secret.
        """
        if not webhook_secret:
            # Fall back to platform webhook secret if workspace-specific not set
            webhook_secret = os.getenv('RAZORPAY_WEBHOOK_SECRET', '')

        if not webhook_secret:
            logger.warning("[Razorpay Webhook] No webhook secret configured.")
            return False

        try:
            generated = hmac.new(
                webhook_secret.encode('utf-8'),
                payload_bytes,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(generated, signature or '')
        except Exception as e:
            logger.error(f"[Razorpay Webhook] Signature error: {e}")
            return False

    # ─── Refunds ─────────────────────────────────────────────────────────────

    @staticmethod
    def initiate_refund(rzp_connection, payment_id: str, amount_inr: float = None, notes: dict = None) -> dict:
        """
        Initiate a refund for a payment using the workspace's own Razorpay credentials.
        amount_inr=None means full refund.
        """
        if not rzp_connection or not rzp_connection.is_connected():
            raise ValueError("Razorpay is not connected for this workspace.")

        key_id     = rzp_connection.linked_key_id
        key_secret = rzp_connection.linked_key_secret

        payload = {}
        if amount_inr is not None:
            payload['amount'] = int(float(amount_inr) * 100)
        if notes:
            payload['notes'] = notes

        try:
            res = requests.post(
                f"{RAZORPAY_API_BASE}/payments/{payment_id}/refund",
                json=payload,
                auth=(key_id, key_secret),
                timeout=15,
            )
            data = res.json()
        except Exception as e:
            logger.error(f"[Razorpay Refund] API error: {e}")
            raise ConnectionError(f"Refund request failed: {str(e)}")

        if res.status_code in [200, 201] and 'id' in data:
            logger.info(f"[Razorpay Refund] Refund {data['id']} initiated for payment {payment_id}")
            return {
                'refund_id':     data['id'],
                'amount':        data.get('amount', 0) / 100,
                'status':        data.get('status'),
                'created_at':    data.get('created_at'),
            }
        else:
            err = data.get('error', {}).get('description', 'Refund failed')
            logger.error(f"[Razorpay Refund] Error: {data}")
            raise ValueError(err)

    # ─── Generate unique state token ─────────────────────────────────────────

    @staticmethod
    def generate_state_token(client_id: int) -> str:
        """Generate a secure random state token for OAuth CSRF protection."""
        random_part = secrets.token_urlsafe(24)
        return f"{client_id}_{random_part}"

    @staticmethod
    def parse_state_token(state: str) -> int | None:
        """Extract client_id from state token."""
        try:
            return int(state.split('_')[0])
        except (ValueError, IndexError):
            return None
