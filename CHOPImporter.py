from math import ceil
import traceback
import requests as r
import urllib3
import json
import sys

from config import (
    CHOP_API_BASE_URL,
    CHOP_REVISION,
    CHOP_YEAR,
    CLIENT_ID,
    CLIENT_SECRET,
    GET_TOKEN_URL,
    I14Y_API_BASE_URL,
    I14Y_PUBLIC_API_BASE_URL,
    I14Y_THEME_CODE,
    I14Y_USER_AGENT,
    RESPONSIBLE_DEPUTY_EMAIL,
    RESPONSIBLE_DEPUTY_FAMILYNAME,
    RESPONSIBLE_DEPUTY_GIVENNAME,
    RESPONSIBLE_PERSON_EMAIL,
    RESPONSIBLE_PERSON_FAMILYNAME,
    RESPONSIBLE_PERSON_GIVENNAME,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Session used for all API calls, so that every call sends our User-Agent
session = r.Session()
session.headers["User-Agent"] = I14Y_USER_AGENT


class CHOPImporter:

    def __init__(self, year, revision, chunk_size=250):
        self.token = self.get_access_token()
        self.year = year
        self.revision = revision
        self.chunk_size = chunk_size
        self.concept_id = None

    def get_access_token(self):
        """Generated an access token from client key and client secret"""
        data = {"grant_type": "client_credentials"}
        response = session.post(
            GET_TOKEN_URL,
            data=data,
            verify=False,
            auth=(CLIENT_ID, CLIENT_SECRET),
        )
        if response.status_code >= 400:
            raise Exception("Failed to get token")
        return "Bearer " + response.json()["access_token"]

    def post_codeListEntries(self, concept_id):
        all_codelists = self.get_chop_codeListEntries()["codeListEntries"]

        total = len(all_codelists)
        print(f"Total codelist entries: {total}")

        num_chunks = ceil(total / self.chunk_size)

        headers = {"Authorization": self.token, "Content-Type": "application/json"}

        for i in range(num_chunks):
            start = i * self.chunk_size
            end = start + self.chunk_size
            chunk = all_codelists[start:end]

            print(f"Uploading chunk {i+1}/{num_chunks} ({len(chunk)} entries)...")

            # The /imports endpoint only accepts a concept without entries, so we use the endpoint
            # that adds entries to an existing concept to upload the chunks one after the other
            response = session.post(
                f"{I14Y_API_BASE_URL}/concepts/{concept_id}/codelist-entries",
                headers=headers,
                data=json.dumps({"data": chunk}, ensure_ascii=False).encode("utf-8"),
                verify=False,
            )

            try:
                response.raise_for_status()
                print(f"\tChunk {i+1} uploaded successfully")
            except r.exceptions.HTTPError as e:
                print(f"\tChunk {i+1} failed: {e}")
                print(f"\tResponse: {response.text}")
                raise

    def publish_i14y(self, public=False):

        chop_data = self.build_data()
        headers = {"Authorization": self.token, "Content-Type": "application/json"}
        response = session.post(
            I14Y_API_BASE_URL + "/concepts",
            json={"data": chop_data},
            headers=headers,
            verify=False,
        )

        if response.status_code >= 400:
            print("Status code:", response.status_code)
            try:
                print("Response JSON:", response.json())
            except ValueError:
                print("Response text:", response.text)
            response.raise_for_status()

        concept_id = response.text.strip('"')
        self.concept_id = concept_id
        print(f"Newly created concept id: {concept_id}")

        if public:
            self.change_publication_level(concept_id, "Public")

        self.post_codeListEntries(concept_id)

        return concept_id

    def change_publication_level(self, concept_id, publication_level):
        response = session.put(
            url=f"{I14Y_API_BASE_URL}/concepts/{concept_id}/publication-level",
            params={"level": publication_level},
            headers={
                "Authorization": self.token,
                "Content-Type": "application/json",
                "Accept": "*/*",
                "Accept-encoding": "json",
            },
            verify=False,
        )
        response.raise_for_status()

    def debug_save_dict_to_json(self, data: dict, filepath: str, indent: int = 4):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)

    def debug_delete_concept(self, concept_id):
        headers = {"Authorization": self.token, "Content-Type": "application/json"}
        try:
            self.change_publication_level(concept_id, "Internal")
        except Exception as e:
            # If concept is already internal we have an exception so we try to delete anyway
            pass
        response = session.delete(I14Y_API_BASE_URL + "/concepts/" + concept_id, headers=headers, verify=False)
        response.raise_for_status()
        print(f"Deleted concept with id {concept_id}")

    def get_chop_codeListEntries(self):
        """
        returns {
            'codeListEntries':
                [{...}]
            }
        """
        url = f"{CHOP_API_BASE_URL}/chop/{self.year}/{self.revision}"
        response = session.get(url, verify=False)
        response.raise_for_status()

        data = response.json()

        # I14Y rejects annotations whose "text" has no language filled (e.g. CodeWithoutPunctuation,
        # CODABLE, LATERAL come with "text": {}), so we drop empty texts
        for entry in data["codeListEntries"]:
            for annotation in entry.get("annotations") or []:
                text = annotation.get("text")
                if text is not None and not any((value or "").strip() for value in text.values()):
                    del annotation["text"]

        return data

    def get_latest_existing_concept(self):
        """
        Fetch the existing DV_CHOP concepts from the public I14Y API
        and return the most recent one (highest version).
        Its name (with the year replaced) and description are reused for the new concept.
        """
        response = session.get(
            f"{I14Y_PUBLIC_API_BASE_URL}/concepts",
            params={"conceptIdentifier": "DV_CHOP", "page": 1, "pageSize": 100},
            verify=False,
        )
        response.raise_for_status()
        concepts = response.json().get("data", [])
        if not concepts:
            raise Exception("No existing DV_CHOP concept found, cannot reuse its description")

        def version_key(concept):
            return tuple(int(part) for part in concept["version"].split("."))

        latest = max(concepts, key=version_key)
        print(f"Reusing description from existing concept version {latest['version']} (id {latest['id']})")
        return latest

    def build_data(self):
        latest_concept = self.get_latest_existing_concept()
        latest_year = latest_concept["version"].split(".")[0]
        data = {
            "name": {
                lang: name.replace(latest_year, str(self.year))
                for lang, name in latest_concept["name"].items()
            },
            "description": latest_concept["description"],
        }
        data["identifiers"] = ["DV_CHOP"]
        data["version"] = f"{self.year}.{self.revision}.0"
        data["themes"] = [{"code": I14Y_THEME_CODE}]
        data["validFrom"] = f"{self.year-1}-12-31T23:00:00+00:00"
        data["validTo"] = f"{self.year}-12-30T23:00:00+00:00"
        data["codeListEntryDefaultSortProperty"] = "Position"
        data["codeListEntryValueMaxLength"] = 8
        data["codeListEntryValueType"] = "String"
        data["conceptType"] = "CodeList"
        data["publisher"] = {"identifier": "CH1"}

        data["responsibleDeputy"] = {
            "givenName": RESPONSIBLE_DEPUTY_GIVENNAME,
            "familyName": RESPONSIBLE_DEPUTY_FAMILYNAME,
            "email": RESPONSIBLE_DEPUTY_EMAIL,
        }

        data["responsiblePerson"] = {
            "givenName": RESPONSIBLE_PERSON_GIVENNAME,
            "familyName": RESPONSIBLE_PERSON_FAMILYNAME,
            "email": RESPONSIBLE_PERSON_EMAIL,
        }

        return data


if __name__ == "__main__":
    importer = CHOPImporter(int(CHOP_YEAR), int(CHOP_REVISION), chunk_size=250)
    try:
        importer.publish_i14y(public=False)
    except Exception:
        traceback.print_exc()
        if importer.concept_id:
            importer.debug_delete_concept(importer.concept_id)
        sys.exit(1)
    print(f"Concept id: {importer.concept_id}")
