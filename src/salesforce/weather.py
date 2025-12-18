import base64
from os.path import basename, splitext
from .base import SalesforceBaseClient


class SFWeatherClient(SalesforceBaseClient):
    """Client for managing weather data in Salesforce."""

    def find_or_create_report(self, pdf_hash: str):
        """
        Finds Weather_Report__c records by PDF hash.
        If none found, creates a new record.

        Args:
            pdf_hash: The hash of the PDF to search for.

        Returns:
            A list of matching records.
        """

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

    def update_forecast(self, record_id: str, forecast_text: str):
        """
        Updates the Forecast__c field of the given Weather_Report__c record.

        Args:
            record_id: The Id of the Weather_Report__c record.
            forecast_text: The forecast text to set.

        Returns:
            True if update succeeded, else False.
        """

        fields = {"Forecast__c": forecast_text}
        return self.update("Weather_Report__c", record_id, fields)
