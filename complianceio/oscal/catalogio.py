import json
from typing import List


class Catalog(object):
    """Represent a catalog"""

    def __init__(self, source):
        try:
            self.oscal = self._load_catalog_json(source)
            json.dumps(self.oscal)
            self.status = "ok"
            self.status_message = "Success loading catalog"
            self.catalog_id = self.oscal.get("id")
            self.info = {}
            self.info["groups"] = self.get_groups()
        except Exception:
            self.oscal = None
            self.status = "error"
            self.status_message = "Error loading catalog"
            self.catalog_id = None
            self.info = {}
            self.info["groups"] = None

    def _load_catalog_json(self, source):
        """Read catalog file - JSON"""
        oscal: dict = {}
        with open(source, "r") as f:
            oscal = json.load(f)
        return oscal.get("catalog")

    def find_dict_by_value(self, search_in, search_key: str, search_value: str):
        """
        Return the dictionary in an array of dictionaries with a key matching a value
        :param search_in: a list of dicts to search in
        :param search_key: the key to search for
        :param search_value: the value to search for
        :return: return a dict containing the search_value
        """
        if search_in is not None:
            results = next(
                (
                    s
                    for s in search_in
                    if search_key in s and s.get(search_key) == search_value
                ),
                None,
            )
        return results

    # Groups
    def get_groups(self) -> List:
        groups: List[dict] = []
        if self.oscal and "groups" in self.oscal:
            groups = self.oscal["groups"]
        return groups

    def get_group_ids(self):
        groups = self.get_groups()
        ids = [item.get("id") for item in groups]
        return ids

    def get_group_title_by_id(self, id):
        group = self.find_dict_by_value(self.get_groups(), "id", id)
        if group is None:
            return None
        return group.get("title")

    def get_group_id_by_control_id(self, control_id) -> str:
        """Return group id given id of a control"""
        group_ids = self.get_group_ids()
        gid: str = ""
        if group_ids:
            for g in group_ids:
                if g.lower() == control_id[:2].lower():
                    gid = g
        return gid

    # Controls
    def get_controls(self) -> List:
        controls: List[dict] = []
        for group in self.get_groups():
            controls += [c for c in group.get("controls")]
        return controls

    def get_control_ids(self) -> List:
        search_collection = self.get_controls()
        return [item.get("id") for item in search_collection]

    def get_controls_all(self) -> List:
        controls: List[dict] = []
        for group in self.get_groups():
            for c in group.get("controls"):
                controls.append(c)
                if "controls" in c:
                    controls += [ce for ce in c.get("controls")]
        return controls

    def get_controls_all_ids(self) -> List:
        search_collection = self.get_controls_all()
        return [item["id"] for item in search_collection]

    def get_control_by_id(self, control_id: str) -> dict:
        """
        Return the dictionary in an array of dictionaries with a key matching a value
        """
        search_array = self.get_controls_all()
        search_key = "id"
        search_value = control_id
        result_dict: dict = next(
            (
                s
                for s in search_array
                if search_key in s and s[search_key] == search_value
            ),
            {},
        )
        return result_dict

    def get_control_statement(self, control: dict) -> str:
        statement = self.get_control_part_by_name(control, "statement")
        lines: List[str] = []
        part: List[str] = []
        if statement:
            if "parts" in statement:
                part = self.__get_parts(statement.get("parts"))
            if part:
                lines.extend(part)
        return "\n".join(lines)

    def __get_parts(self, parts) -> List:
        lines: List[str] = []
        for p in parts:
            if "prose" in p:
                label = self.get_control_property_by_name(p, "label")
                prose = p.get("prose")
                lines.append(f"{label} {prose}")
            part: List[str] = []
            if "parts" in p:
                part = self.__get_parts(p.get("parts"))
            if part:
                lines.extend(part)
        return lines

    # Params
    def get_control_parameters(self, control: dict) -> dict:
        """Return the guidance prose for a control property"""
        return self.__get_control_parameter_values(control)

    def get_control_parameter_label_by_id(self, control: dict, param_id: str) -> str:
        """Return value of a parameter of a control by id of parameter"""
        param = self.find_dict_by_value(control.get("params"), "id", param_id)
        return param.get("label")

    # Props
    def get_control_property_by_name(self, control: dict, property_name: str) -> str:
        """Return value of a property of a control by name of property"""
        value: str = ""
        if control is None:
            return None
        prop = self.find_dict_by_value(control.get("props"), "name", property_name)
        if prop is not None:
            value = prop.get("value")
        return value

    def get_control_part_by_name(self, control: dict, part_name: str) -> dict:
        """Return value of a part of a control by name of part"""
        part: dict = {}
        if "parts" in control:
            part = self.find_dict_by_value(control.get("parts"), "name", part_name)
        return part

    def get_resource_by_uuid(self, uuid: str) -> dict:
        resource: dict = {}
        if "back-matter" in self.oscal and "resources" in self.oscal.get("back-matter"):
            resources = self.oscal.get("back-matter").get("resources")
            resource = self.find_dict_by_value(resources, "uuid", uuid)
        return resource

    def __get_control_parameter_values(self, control) -> dict:
        params: dict = {}
        if "params" in control:
            for p in control.get("params"):
                pid = p.get("id")
                if "values" in p:
                    params[pid] = p.get("values")
                elif "select" in p:
                    select = p.get("select")
                    howmany = select.get("how-many") if "how-many" in select else 1
                    params[pid] = {
                        howmany: select.get("choice"),
                    }
                else:
                    params[pid] = p.get("label")
        return params

    @property
    def catalog_title(self) -> str:
        metadata = self.oscal.get("metadata", {})
        return metadata.get("title", "")
