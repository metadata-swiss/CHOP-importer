# CHOP-importer

This repo contains a script that imports CHOP as a concept in I14Y.

The required pip modules are listed in the `requirements.txt` file.

You have to create a `.env` file with the same variables as in `.env.example`.

The following env variables are needed:
- `I14Y_API_BASE_URL`: i14y api url (different for ABN/DEV/PRD)
- `GET_TOKEN_URL`: url to generate i14y token (different for ABN/DEV/PRD)
- `CLIENT_ID`: client id to generate i14y token
- `CLIENT_SECRET`: client secret to generate i14y token
- `CHOP_API_BASE_URL`: MCT API url
- `CHOP_YEAR`: Chop year
- `CHOP_REVISION`: Chop revision (usually 99)
- `RESPONSIBLE_DEPUTY_GIVENNAME`: Given name for responsible deputy
- `RESPONSIBLE_DEPUTY_FAMILYNAME`: Family name for responsible deputy
- `RESPONSIBLE_DEPUTY_EMAIL`: Email for responsible deputy
- `RESPONSIBLE_PERSON_GIVENNAME`: Given name for responsible person
- `RESPONSIBLE_PERSON_FAMILYNAME`: Family name for responsible person
- `RESPONSIBLE_PERSON_EMAIL`: Email for responsible person
- `I14Y_PUBLIC_API_BASE_URL` (optional): public i14y api used to read the existing `DV_CHOP` concepts (default `https://api.i14y.admin.ch/api`)

The CHOP API provides the codeListEntries. The title and description of the concept are taken from the most recent existing `DV_CHOP` concept (highest version) returned by the public i14y API: the description is copied as-is, and in the title the year of that concept is replaced by the provided `CHOP_YEAR`.

## GitHub Actions

The workflow `.github/workflows/import_chop.yml` can be started manually (*Actions > I14Y CHOP Importer > Run workflow*) with the inputs `environment` (`ABN` or `PRD`), `year` and `revision`.

Each target needs a GitHub Environment (*Settings > Environments*) named `ABN` / `PRD` with:
- secrets: `CLIENT_ID`, `CLIENT_SECRET`, `RESPONSIBLE_DEPUTY_GIVENNAME`, `RESPONSIBLE_DEPUTY_FAMILYNAME`, `RESPONSIBLE_DEPUTY_EMAIL`, `RESPONSIBLE_PERSON_GIVENNAME`, `RESPONSIBLE_PERSON_FAMILYNAME`, `RESPONSIBLE_PERSON_EMAIL` (secrets so they are masked in the public workflow logs)
- variables: `I14Y_API_BASE_URL`, `GET_TOKEN_URL`

The runner must be able to reach the MCT API (`CHOP_API_BASE_URL`).

Parameters for the I14Y concept that are unlikely to change are defined in the `build_data` function in `CHOPImporter.py` file.