#
# helpers for constructing OSCAL structures
# serializing as JSON
#
# elements common to component and SSP models
import re
from datetime import datetime
from datetime import timezone
from enum import Enum
from typing import List
from typing import Optional
from uuid import UUID
from uuid import uuid4

from pydantic import BaseModel
from pydantic import Field

OSCAL_VERSION = "1.0.0-RC1"


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
                if not d.get(key, False):
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


class BackMatter(OSCALElement):
    resources: Optional[List[Resource]]


class Email(str):
    pass


class Revision(OSCALElement):
    title: Optional[str]
    published: Optional[datetime]
    last_modified: Optional[datetime]
    version: Optional[str]
    oscal_version: Optional[str]
    properties: Optional[List[Property]]

    class Config:
        fields = {"last_modified": "last-modified", "oscal_version": "oscal-version"}
        allow_population_by_field_name = True


class PartyTypeEnum(str, Enum):
    person = "person"
    organization = "organization"


class Party(OSCALElement):
    uuid: UUID = Field(default_factory=uuid4)
    type: PartyTypeEnum
    party_name: str
    short_name: Optional[str]
    properties: Optional[List[Property]]
    email_addresses: Optional[List[Email]]

    class Config:
        fields = {
            "party_name": "party-name",
            "short_name": "short-name",
            "email_addresses": "email-addresses",
        }
        allow_population_by_field_name = True


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


class Metadata(OSCALElement):
    title: str
    version: str
    oscal_version: str = OSCAL_VERSION
    published: datetime = datetime.now(timezone.utc)
    last_modified: datetime = datetime.now(timezone.utc)
    properties: Optional[List[Property]]
    parties: Optional[List[Party]]
    links: Optional[List[Link]]
    revision_history: Optional[List[Revision]]

    class Config:
        fields = {
            "oscal_version": "oscal-version",
            "last_modified": "last-modified",
            "revision_history": "revision-history",
        }
        allow_population_by_field_name = True
