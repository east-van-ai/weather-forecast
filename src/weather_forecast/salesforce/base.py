# =======================================================================
# weather-forecast -- JMA weather chart to Salesforce, no cloud required.
# East Van AI -- AI for the rest of us!
# https://github.com/east-van-ai
# ========================================================================
"""
Salesforce OAuth2 (JWT Bearer) Login — No Browser, No Redirect

Flow:
1. Build a signed JSON Web Token(JWT) assertion using your private key.
2. Send it to Salesforce's /token endpoint with grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer
3. Receive access token.
4. Create a simple_salesforce client.
"""

import time
import jwt
import requests
from simple_salesforce import Salesforce


class SalesforceBaseClient:
    """Base Salesforce client using JWT Bearer OAuth2 flow."""

    def __init__(self, config: dict = {}):
        self.client_id = config["client_id"]
        self.username = config["username"]
        self.audience = config["audience"]
        self.private_key = config["private_key"]

        self.sf = None
        self._authenticate()

    def _create_jwt_assertion(self):
        """
        Creates a JWT assertion signed with the private key.
        Returns the JWT as a string.
        """
        now = int(time.time())
        exp = now + 300  # 5 minutes

        payload = {
            "iss": self.client_id,
            "sub": self.username,
            "aud": self.audience,
            "exp": exp,
        }

        return jwt.encode(payload, self.private_key, algorithm="RS256")

    def _authenticate(self):
        """
        Authenticates with Salesforce using JWT Bearer flow.
        Sets up the simple_salesforce client.
        """
        jwt_assertion = self._create_jwt_assertion()

        token_url = f"{self.audience}/services/oauth2/token"

        payload = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": jwt_assertion,
        }

        response = requests.post(token_url, data=payload)
        response.raise_for_status()

        tokens = response.json()
        access_token = tokens["access_token"]
        instance_url = tokens["instance_url"]

        # Create a simple_salesforce client
        self.sf = Salesforce(
            session_id=access_token,
            instance_url=instance_url,
        )

    # --------------------------------------------------
    # Public Helpers
    # --------------------------------------------------
    def query(self, soql: str):
        """Run a SOQL query and return list of records."""
        result = self.sf.query(soql)
        return result.get("records", [])

    def create(self, object_name: str, fields: dict):
        """Create a new Salesforce record."""
        return self.sf.__getattr__(object_name).create(fields)

    def update(self, object_name: str, record_id: str, fields: dict):
        """Update Salesforce record."""
        return self.sf.__getattr__(object_name).update(record_id, fields)

    def get(self, object_name: str, record_id: str):
        """Fetch a single record."""
        return self.sf.__getattr__(object_name).get(record_id)

    def upsert(
        self,
        object_name: str,
        external_id_field: str,
        external_id_value: str,
        fields: dict,
    ):
        """Upsert a Salesforce record using an external ID."""
        result = self.sf.__getattr__(object_name).upsert(
            f"{external_id_field}/{external_id_value}", fields
        )

        created = str(result) == "201"  # HTTP 201 Created / 200 OK (Update)

        soql = (
            f"SELECT Id FROM {object_name} "
            f"WHERE {external_id_field} = '{external_id_value}'"
        )
        records = self.query(soql)

        record_id = records[0]["Id"] if records else None

        return {
            "created": created,
            "record_id": record_id,
        }
