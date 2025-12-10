"""
Salesforce OAuth2 (JWT Bearer) Login — No Browser, No Redirect

Flow:
1. Build a signed JSON Web Token(JWT) assertion using your private key.
2. Send it to Salesforce's /token endpoint with grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer
3. Receive access token.
4. Create a simple_salesforce client.
"""

import os
import time
import jwt
import requests
from simple_salesforce import Salesforce
from dotenv import load_dotenv
import base64
from os.path import basename, splitext

load_dotenv()


class SalesforceClient:
    def __init__(self):
        self.client_id = os.getenv("SF_CLIENT_ID")
        self.username = os.getenv("SF_USERNAME")
        self.audience = os.getenv("SF_AUDIENCE", "https://login.salesforce.com")
        private_key_path = os.getenv("SF_PRIVATE_KEY_PATH")

        # TODO: validate env vars

        with open(private_key_path, "rb") as f:
            self.private_key = f.read()

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

    def find_or_create_records(self, pdf_hash: str):
        if not pdf_hash:
            return []

        # Escape single quotes for SOQL safety
        escaped_hash = pdf_hash.replace("'", "\\'")

        query = (
            "SELECT Id, Name, PDF_Hash__c, Forecast__c, Chart_Image_Id__c "
            f"FROM Weather_Report__c WHERE PDF_Hash__c = '{escaped_hash}' LIMIT 1"
        )

        records = self.query(query)

        if not records:
            self.create(
                "Weather_Report__c",
                {
                    "Name": "DEV Weather Report",
                    "PDF_Hash__c": pdf_hash,
                },
            )
            # Re-query to return the new record
            records = self.query(query)

        return records

    def ensure_small_png(self, record_id: str, file_path: str) -> str | None:
        """
        Ensures that a file named 'small.png', or a desired title, is linked to the given Salesforce record.
        If a ContentVersion with Title='small' already exists, no upload happens.

        Returns:
            ContentVersion Id if a new file was uploaded,
            None if it already existed.
        """
        # Salesforce strips extensions -> Title = "small"
        desired_title, _ = splitext(basename(file_path))

        # 1. Find ContentDocumentLinks pointing to this record
        link_query = f"""
        SELECT ContentDocumentId
        FROM ContentDocumentLink
        WHERE LinkedEntityId = '{record_id}'
        """
        links = self.query(link_query)

        # 2. Scan each linked ContentDocument for ContentVersion with the desired Title
        for link in links:
            cd_id = link["ContentDocumentId"]

            version_query = f"""
            SELECT Title
            FROM ContentVersion
            WHERE ContentDocumentId = '{cd_id}'
            ORDER BY CreatedDate DESC
            LIMIT 1
            """
            versions = self.query(version_query)

            if versions:
                title = versions[0]["Title"]
                if title == desired_title:
                    # Found an existing "small"
                    return None

        # 3. File not found -> upload a new ContentVersion
        with open(file_path, "rb") as f:
            raw = f.read()

        b64_data = base64.b64encode(raw).decode()

        body = {
            "Title": desired_title,
            "PathOnClient": basename(file_path),
            "VersionData": b64_data,
            "FirstPublishLocationId": record_id,
        }

        # Create ContentVersion
        new_version_id = self.sf.ContentVersion.create(body)["id"]
        return new_version_id

    def update_forecast(self, record_id: str, forecast_text: str):
        fields = {"Forecast__c": forecast_text}
        return self.update("Weather_Report__c", record_id, fields)

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
