#
# helpers for constructing OSCAL structures
# serializing as JSON
#
# elements common to component and SSP models
import re
from datetime import datetime
from datetime import timezone
from enum import Enum
from typing import Dict
from typing import List
from typing import Optional
from uuid import UUID
from uuid import uuid4

from pydantic import BaseModel
from pydantic import Field

OSCAL_VERSION = "1.0.0"


class ControlRegExps:
    nist_800_171 = re.compile(r"^\d+\.\d+(\.\d+)*$")
    nist_800_53_simple = re.compile(r"^([a-z]{2})-(\d+)$")
    nist_800_53_extended = re.compile(r"^([a-z]{2})-(\d+)\s*\((\d+)\)$")
    nist_800_53_part = re.compile(r"^([a-z]{2})-(\d+)\.([a-z]+)$")
    nist_800_53_extended_part = re.compile(r"^([a-z]{2})-(\d+)\s*\((\d+)\)\.([a-z]+)$")


def oscalize_control_id(control_id):
    """
    output an oscal standard control id from various common formats for control ids
    """

    control_id = control_id.strip()
    control_id = control_id.lower()

    # 1.2, 1.2.3, 1.2.3.4, etc.
    if re.match(ControlRegExps.nist_800_171, control_id):
        return control_id

    # AC-1
    match = re.match(ControlRegExps.nist_800_53_simple, control_id)
    if match:
        family = match.group(1)
        number = int(match.group(2))
        return f"{family}-{number}"

    # AC-2(1)
    match = re.match(ControlRegExps.nist_800_53_extended, control_id)
    if match:
        family = match.group(1)
        number = int(match.group(2))
        extension = int(match.group(3))
        return f"{family}-{number}.{extension}"

    # AC-1.a
    match = re.match(ControlRegExps.nist_800_53_part, control_id)
    if match:
        family = match.group(1)
        number = int(match.group(2))
        return f"{family}-{number}"

    # AC-2(1).b
    match = re.match(ControlRegExps.nist_800_53_extended_part, control_id)
    if match:
        family = match.group(1)
        number = int(match.group(2))
        extension = int(match.group(3))
        return f"{family}-{number}.{extension}"

    return control_id


def control_to_statement_id(control_id):
    """
    Construct an OSCAL style statement ID from a control identifier.
    """

    control_id = control_id.strip()
    control_id = control_id.lower()

    # 1.2, 1.2.3, 1.2.3.4, etc.
    if re.match(ControlRegExps.nist_800_171, control_id):
        return f"{control_id}_smt"

    # AC-1
    match = re.match(ControlRegExps.nist_800_53_simple, control_id)
    if match:
        family = match.group(1)
        number = int(match.group(2))
        return f"{family}-{number}_smt"

    # AC-2(1)
    match = re.match(ControlRegExps.nist_800_53_extended, control_id)
    if match:
        family = match.group(1)
        number = int(match.group(2))
        extension = int(match.group(3))
        return f"{family}-{number}.{extension}_smt"

    # AC-1.a
    match = re.match(ControlRegExps.nist_800_53_part, control_id)
    if match:
        family = match.group(1)
        number = int(match.group(2))
        part = match.group(3)
        return f"{family}-{number}_smt.{part}"

    # AC-2(1).b
    match = re.match(ControlRegExps.nist_800_53_extended_part, control_id)
    if match:
        family = match.group(1)
        number = int(match.group(2))
        extension = int(match.group(3))
        part = match.group(4)
        return f"{family}-{number}.{extension}_smt.{part}"

    # nothing matched ...
    return f"{control_id}_smt"


class NCName(str):
    pass


class MarkupLine(str):
    pass


class MarkupMultiLine(str):
    pass


class OSCALElement(BaseModel):
    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)
        if hasattr(self.Config, "container_assigned"):
            for key in self.Config.container_assigned:
                if key in d:
                    del d[key]
        if hasattr(self.Config, "exclude_if_false"):
            for key in self.Config.exclude_if_false:
                if not d.get(key, False) and key in d:
                    del d[key]
        return d


class Property(OSCALElement):
    name: str
    value: str
    uuid: UUID = Field(default_factory=uuid4)


class Resource(OSCALElement):
    uuid: UUID = Field(default_factory=uuid4)
    title: Optional[str]
    description: Optional[MarkupMultiLine]
    props: Optional[List[Property]]
    remarks: Optional[MarkupMultiLine]

    # missing: annotations, document-ids, citation, rlinks, base64


class LinkRelEnum(str, Enum):
    homepage = "homepage"
    interview_notes = "interview-notes"
    tool_output = "tool-output"
    photograph = "photograph"
    questionaire = "questionaire"
    screen_shot = "screen-shot"


class Link(OSCALElement):
    text: str
    href: str
    rel: Optional[LinkRelEnum]
    media_type: Optional[str]

    class Config:
        fields = {"media_type": "media-type"}
        allow_population_by_field_name = True


class Annotation(OSCALElement):
    name: NCName
    uuid: Optional[UUID]
    ns: Optional[str]  # really a URI
    value: str
    remarks: Optional[MarkupMultiLine]


class BackMatter(OSCALElement):
    resources: Optional[List[Resource]]


class EmailAddress(str):
    pass


class TelephoneNumber(OSCALElement):
    type: Optional[str]
    number: str


class Revision(OSCALElement):
    title: Optional[str]
    published: Optional[datetime]
    last_modified: Optional[datetime]
    version: Optional[str]
    oscal_version: Optional[str]
    props: Optional[List[Property]]

    class Config:
        fields = {"last_modified": "last-modified", "oscal_version": "oscal-version"}
        allow_population_by_field_name = True


class DocumentId(OSCALElement):
    scheme: str  # really, URI
    identifier: str


class PartyTypeEnum(str, Enum):
    person = "person"
    organization = "organization"


class Party(OSCALElement):
    uuid: UUID = Field(default_factory=uuid4)
    type: PartyTypeEnum
    name: Optional[str]
    short_name: Optional[str]
    props: Optional[List[Property]]
    annotations: Optional[List[Annotation]]
    links: Optional[List[Link]]
    email_addresses: Optional[List[EmailAddress]]
    telephone_numbers: Optional[List[TelephoneNumber]]
    remarks: Optional[MarkupMultiLine]

    class Config:
        fields = {
            "party_name": "party-name",
            "short_name": "short-name",
            "email_addresses": "email-addresses",
            "telephone_numbers": "telephone-numbers",
        }
        allow_population_by_field_name = True


class Location(OSCALElement):
    pass


class RoleIDEnum(str, Enum):
    asset_administrator = "asset-administrator"
    asset_owner = "asset-owner"
    authorizing_official = "authorizing-official"
    authorizing_official_poc = "authorizing-official-poc"
    configuration_management = "configuration-management"
    content_approver = "content-approver"
    help_desk = "help-desk"
    incident_response = "incident-response"
    information_system_security_officer = "information-system-security-officer"
    maintainer = "maintainer"
    network_operations = "network-operations"
    prepared_by = "prepared_by"
    prepared_for = "prepared_for"
    privacy_poc = "privacy-poc"
    provider = "provider"
    security_operations = "security-operations"
    system_owner = "system-owner"
    system_owner_poc_management = "system-owner-poc-management"
    system_owner_poc_other = "system-owner-poc-other"
    system_owner_poc_technical = "system-owner-poc-technical"


class Role(OSCALElement):
    id: RoleIDEnum
    title: MarkupLine
    short_name: Optional[str]
    description: Optional[MarkupMultiLine]
    props: Optional[List[Property]]
    annotations: Optional[List[Annotation]]
    links: Optional[List[Link]]
    remarks: Optional[MarkupMultiLine]


class ResponsibleParty(OSCALElement):
    role_id: RoleIDEnum
    party_uuids: List[UUID]
    props: Optional[List[Property]]
    links: Optional[List[Link]]
    remarks: Optional[MarkupMultiLine]

    class Config:
        fields = {"party_uuids": "party-uuids"}
        allow_population_by_field_name = True


class Metadata(OSCALElement):
    title: str
    published: datetime = datetime.now(timezone.utc)
    last_modified: datetime = datetime.now(timezone.utc)
    version: str
    oscal_version: str = OSCAL_VERSION
    revisions: Optional[List[Revision]]
    document_ids: Optional[List[DocumentId]]
    props: Optional[List[Property]]
    links: Optional[List[Link]]
    roles: Optional[List[Role]]
    locations: Optional[List[Location]]
    parties: Optional[List[Party]]
    responsible_parties: Optional[List[ResponsibleParty]]
    remarks: Optional[MarkupMultiLine]

    class Config:
        fields = {
            "oscal_version": "oscal-version",
            "document_ids": "document-ids",
            "last_modified": "last-modified",
            "responsible_parties": "responsible-parties",
        }
        exclude_if_false = ["responsible-parties"]
        allow_population_by_field_name = True


class SetParameter(OSCALElement):
    param_id: NCName
    values: List[str] = []
    remarks: Optional[MarkupMultiLine]

    class Config:
        allow_population_by_field_name = True
        container_assigned = ["param_id"]


class ResponsibleRole(OSCALElement):
    role_id: RoleIDEnum
    props: Optional[List[Property]]
    links: Optional[List[Link]]
    party_uuids: Optional[List[UUID]]
    remarks: Optional[MarkupMultiLine]

    class Config:
        fields = {"party_uuids": "party-uuids"}
        allow_population_by_field_name = True
