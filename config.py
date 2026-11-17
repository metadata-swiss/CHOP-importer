import os
from dotenv import load_dotenv

load_dotenv()

CHOP_API_BASE_URL = "https://www.mct.bfs.admin.ch/api/Iop"
# Public I14Y API used to read the existing DV_CHOP concepts (name and description are taken from the most recent one)
I14Y_PUBLIC_API_BASE_URL = os.environ.get("I14Y_PUBLIC_API_BASE_URL", "https://api.i14y.admin.ch/api")

I14Y_API_BASE_URL = os.environ["I14Y_API_BASE_URL"]
GET_TOKEN_URL = os.environ["GET_TOKEN_URL"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
CHOP_YEAR = os.environ["CHOP_YEAR"]
CHOP_REVISION = os.environ["CHOP_REVISION"]
RESPONSIBLE_DEPUTY_GIVENNAME =  os.environ["RESPONSIBLE_DEPUTY_GIVENNAME"]
RESPONSIBLE_DEPUTY_FAMILYNAME =  os.environ["RESPONSIBLE_DEPUTY_FAMILYNAME"]
RESPONSIBLE_DEPUTY_EMAIL =  os.environ["RESPONSIBLE_DEPUTY_EMAIL"]
RESPONSIBLE_PERSON_GIVENNAME =  os.environ["RESPONSIBLE_PERSON_GIVENNAME"]
RESPONSIBLE_PERSON_FAMILYNAME =  os.environ["RESPONSIBLE_PERSON_FAMILYNAME"]
RESPONSIBLE_PERSON_EMAIL =  os.environ["RESPONSIBLE_PERSON_EMAIL"]