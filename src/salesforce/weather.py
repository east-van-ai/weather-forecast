import base64
from os.path import basename, splitext
from typing import NamedTuple

from .base import SalesforceBaseClient


class ReportUpsertResult(NamedTuple):
    record_id: str
    created: bool


class SFWeatherClient(SalesforceBaseClient):
    """Client for managing weather data in Salesforce."""

    def upsert_report(self, pdf_hash: str, forecast_text: str) -> ReportUpsertResult:
        """
        Upserts Weather_Report__c by PDF hash.

        Args:
            pdf_hash: The hash of the PDF to search for.
            forecast_text: The forecast text to set in the record.

        Returns:
            ReportUpsertResult: record ID and whether it was created.
        """
        if not pdf_hash:
            raise ValueError("pdf_hash must not be empty")

        escaped_hash = pdf_hash.replace("'", "\\'")

        # Using External ID (PDF_Hash__c) to upsert
        # Salesforce returns the ID and created status
        result = self.upsert(
            "Weather_Report__c",
            external_id_field="PDF_Hash__c",
            external_id_value=pdf_hash,
            fields={
                "Name": "DEV Weather Report",
                "Forecast__c": forecast_text,
            },
        )

        return ReportUpsertResult(
            record_id=result["record_id"],
            created=result["created"],
        )

    def ensure_preview_image(self, record_id: str, file_path: str) -> str | None:
        """
        Ensures that a ContentVersion with the given file is linked to the record.
        If such a ContentVersion already exists (by Title), does nothing.

        Args:
            record_id: The Id of the Weather_Report__c record.
            file_path: Path to the PNG file to upload.

        Returns:
            The new ContentVersion Id if uploaded, else None.
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
