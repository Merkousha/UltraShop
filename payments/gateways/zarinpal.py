"""
ZarinPal REST API (v4). Request payment then verify on callback.
Docs: https://docs.zarinpal.com/paymentGateway/
"""
import json
import urllib.request
import urllib.error
from decimal import Decimal

from .base import BaseGateway


class ZarinPalGateway(BaseGateway):
    SANDBOX_URL = "https://sandbox.zarinpal.com/pg/rest/WebGate/"
    PRODUCTION_URL = "https://api.zarinpal.com/pg/rest/WebGate/"

    def __init__(self, merchant_id, sandbox=True):
        self.merchant_id = merchant_id
        self.base_url = self.SANDBOX_URL if sandbox else self.PRODUCTION_URL
        self.start_pay_url = "https://sandbox.zarinpal.com/pg/StartPay/" if sandbox else "https://www.zarinpal.com/pg/StartPay/"

    def _post(self, path, data):
        req = urllib.request.Request(
            self.base_url + path,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode() if e.fp else "{}"
            try:
                return json.loads(body)
            except Exception:
                return {"errors": {"message": body}}
        except Exception as e:
            return {"errors": {"message": str(e)}}

    def request(self, amount_rials, callback_url, description, order_id=None):
        amount = int(Decimal(amount_rials))
        data = {
            "merchant_id": self.merchant_id,
            "amount": amount,
            "callback_url": callback_url,
            "description": description or f"Order #{order_id}",
        }
        resp = self._post("payment_request.json", data)
        if resp.get("data", {}).get("authority"):
            authority = resp["data"]["authority"]
            payment_url = self.start_pay_url + authority
            return True, payment_url, authority, ""
        msg = resp.get("errors", {}).get("message", "Unknown error")
        return False, "", "", str(msg)

    def verify(self, authority, amount_rials):
        amount = int(Decimal(amount_rials))
        data = {
            "merchant_id": self.merchant_id,
            "authority": authority,
            "amount": amount,
        }
        resp = self._post("payment_verification.json", data)
        if resp.get("data", {}).get("ref_id"):
            return True, str(resp["data"]["ref_id"]), ""
        msg = resp.get("errors", {}).get("message", "Verification failed")
        return False, "", str(msg)
