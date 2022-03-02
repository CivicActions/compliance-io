from ast import Str
import json
import os
import re
from collections import defaultdict
from typing import List

from .utilities import de_oscalize_control_id, uhash


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

    def _load_catalog_json(self, source) -> dict:
        """Read catalog file - JSON""" 
        oscal: dict = {}
        with open(source, "r") as f:
            oscal = json.load(f)
        return oscal.get("catalog")

    def find_dict_by_value(self, search_in: list, search_key: str, search_value: str) -> dict:
        """
        Return the dictionary in an array of dictionaries with a key matching a value
        :param search_in: a list of dicts to search in
        :param search_key: the key to search for
        :param search_value: the value to search for
        :return: return a dict containing the search_value
        """
        results: dict = {}
        if search_in is not None:
            results = next(
                (s for s in search_in if search_key in s and s.get(search_key) == search_value), None
            )
        return results

    # Groups
    def get_groups(self) -> List[str]:
        groups: List[str] = []

        if self.oscal and "groups" in self.oscal:
            groups = self.oscal["groups"]
        return groups

    def get_group_ids(self) -> List:
        ids: List[str] = []
        groups = self.get_groups()
        ids = [item["id"] for item in groups]
        return ids

    def get_group_title_by_id(self, id) -> str:
        group = self.find_dict_by_value(self.get_groups(), "id", id)
        if group is None:
            return None
        return group.get("title")

    def get_group_id_by_control_id(self, control_id) -> str:
        """Return group id given id of a control"""
        group_ids = self.get_group_ids()
        gid: Str = None
        if group_ids:
            for g in group_ids:
                if g.lower() == control_id[:2].lower():
                    gid = g
        return gid

    # Controls
    def get_controls(self) -> List:
        controls: List[str] = []
        for group in self.get_groups():
            controls += [control for control in group.get("controls")]
        return controls

    def get_control_ids(self) -> List:
        search_collection = self.get_controls()
        return [item["id"] for item in search_collection]

    def get_controls_all(self) -> List:
        controls: List[str] = []
        for group in self.get_groups():
            for control in group["controls"]:
                controls.append(control)
                if "controls" in control:
                    controls += [control_e for control_e in control["controls"]]
        return controls

    def get_controls_all_ids(self) -> List:
        search_collection = self.get_controls_all()
        return [item["id"] for item in search_collection]

    def get_control_by_id(self, control_id) -> dict:
        """Return the dictionary in an array of dictionaries with a key matching a value"""
        search_array = self.get_controls_all()
        search_key = "id"
        search_value = control_id
        result_dict: dict = next(
            (sub for sub in search_array if sub[search_key] == search_value), None
        )
        return result_dict

    # Params
    def get_control_parameters(self, control) -> dict:
        """Return the guidance prose for a control property"""
        return self.__get_control_parameter_values(control)


    def get_control_parameter_label_by_id(self, control, param_id) -> str:
        """Return value of a parameter of a control by id of parameter"""
        param = self.find_dict_by_value(control.get("params"), "id", param_id)
        return param.get("label")

    # Props
    def get_control_property_by_name(self, control, property_name) -> str:
        """Return value of a property of a control by name of property"""
        if control is None:
            return None
        prop = self.find_dict_by_value(control.get("props"), "name", property_name)
        if prop is None:
            return None
        return prop.get("value")


    def get_control_guidance_links(self, control) -> List:
        """Return the links in the guidance section of a control"""
        guidance = self.get_control_part_by_name(control, "guidance")
        links: List[str] = []
        if guidance and "links" in guidance:
            links = guidance.get("links")
        return links

    def get_guidance_related_links_by_value_in_href(self, control, value):
        """
        Return objects from 'rel': 'related' links with particular value found
        in the 'href' string
        """
        links = [
            link
            for link in self.get_control_guidance_links(control)
            if link.get("rel") == "related" and value in link.get("href")
        ]
        return links

    def get_guidance_related_links_text_by_value_in_href(self, control, value):
        """
        Return 'text' from rel': 'related' links with particular value found in
        the 'href' string
        """
        links_text = [
            link.get("text")
            for link in self.get_control_guidance_links(control)
            if link.get("rel") == "related" and value in link.get("href")
        ]
        return links_text


    def get_flattened_control_as_dict(self, control) -> dict:
        """
        Return a control as a simplified, flattened Python dictionary.
        If parameter_values is supplied, it will override any paramters set
        in the catalog.
        """
        if control is None:
            family_id = None
            description = self.get_control_prose_as_markdown(
                control,
                part_types={"statement"},
                parameter_values=self.__get_control_parameter_values(control),
            )
            description_print = description.replace("\n", "<br/>")
            cl_dict = {
                "id": None,
                "id_display": None,
                "title": None,
                "family_id": family_id,
                "family_title": None,
                "class": None,
                "description": description,
                "description_print": description_print,
                "guidance": None,
                "catalog_key": None,
                "catalog_id": None,
                "sort_id": None,
                "label": None,
                "guidance_links": None,
            }
        else:
            family_id = self.get_group_id_by_control_id(control["id"])
            description = self.get_control_prose_as_markdown(
                control,
                part_types={"statement"},
                parameter_values=self.__get_control_parameter_values(control),
            )
            description_print = description.replace("\n", "<br/>")
            cl_dict = {
                "id": control["id"],
                "id_display": de_oscalize_control_id(control["id"]),
                "title": control["title"],
                "family_id": family_id,
                "family_title": self.get_group_title_by_id(family_id),
                "class": control["class"],
                "description": description,
                "description_print": description_print,
                "guidance": self.get_control_prose_as_markdown(
                    control, part_types={"guidance"}
                ),
                "catalog_key": self.catalog_key,
                "catalog_id": self.catalog_id,
                "sort_id": self.get_control_property_by_name(control, "sort-id"),
                "label": self.get_control_property_by_name(control, "label"),
                "guidance_links": self.get_control_guidance_links(control),
            }
        return cl_dict

    def get_flattened_controls_all_as_dict(self) -> dict:
        """Return all controls as a simplified flattened Python dictionary indexed by control ids"""
        # Create an empty dictionary
        cl_all_dict: dict = {}
        # Get all the controls
        for cl in self.get_controls_all():
            # Get flattened control and add to dictionary of controls
            cl_dict = self.get_flattened_control_as_dict(cl)
            cl_all_dict[cl_dict["id"]] = cl_dict
        return cl_all_dict


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

