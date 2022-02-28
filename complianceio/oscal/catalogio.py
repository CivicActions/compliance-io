import json
import os
import re
from collections import defaultdict
from typing import List

from .utilities import de_oscalize_control_id, uhash


class Catalog(object):
    """Represent a catalog"""
    def GetInstance(cls, catalog_key="CMS_ARS_5_0", parameter_values=dict()):

        catalog_instance_key = Catalog._catalog_instance_key(
            catalog_key, parameter_values
        )

        if not hasattr(cls, catalog_instance_key):
            new_catalog = Catalog(
                catalog_key=catalog_key, parameter_values=parameter_values
            )
            setattr(cls, catalog_instance_key, new_catalog)
        return getattr(cls, catalog_instance_key)

    @staticmethod
    def _catalog_instance_key(catalog_key, parameter_values):
        catalog_instance_key = "_cached_instance_" + catalog_key
        if parameter_values:
            parameter_values_hash = uhash(frozenset(parameter_values.items()))
            catalog_instance_key += "_" + str(parameter_values_hash)
        return catalog_instance_key.replace("-", "_")

    def __init__(self, source, parameter_values=dict()):
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

        # self.parameter_values = parameter_values
        # self.flattened_controls_all_as_dict = self.get_flattened_controls_all_as_dict()
        # self.flattened_controls_all_as_dict_list = (
        #     self.get_flattened_controls_all_as_dict_list()
        # )
        # self.parameters_by_control = self._cache_parameters_by_control()

    def _load_catalog_json(self, source):
        """Read catalog file - JSON"""
        with open(source, 'r') as f:
            oscal = json.load(f)
        return oscal.get("catalog")

    def find_dict_by_value(self, search_array, search_key, search_value):
        """Return the dictionary in an array of dictionaries with a key matching a value"""
        if search_array is None:
            return None
        result_dict = next(
            (sub for sub in search_array if sub[search_key] == search_value), None
        )
        return result_dict


    def get_groups(self):
        if self.oscal and "groups" in self.oscal:
            return self.oscal["groups"]
        else:
            return []

    def get_group_ids(self):
        search_collection = self.get_groups()
        return [item["id"] for item in search_collection]

    def get_group_title_by_id(self, id):
        group = self.find_dict_by_value(self.get_groups(), "id", id)
        if group is None:
            return None
        return group["title"]

    def get_group_id_by_control_id(self, control_id):
        """Return group id given id of a control"""

        group_ids = self.get_group_ids()
        if group_ids:
            for group_id in group_ids:
                if group_id.lower() == control_id[:2].lower():
                    return group_id
        else:
            return None

        return None

    def get_controls(self):
        controls = []
        for group in self.get_groups():
            controls += [control for control in group["controls"]]
        return controls

    def get_control_ids(self):
        search_collection = self.get_controls()
        return [item["id"] for item in search_collection]

    def get_controls_all(self):
        controls = []
        for group in self.get_groups():
            for control in group["controls"]:
                controls.append(control)
                if "controls" in control:
                    controls += [control_e for control_e in control["controls"]]
        return controls

    def get_controls_all_ids(self):
        search_collection = self.get_controls_all()
        return [item["id"] for item in search_collection]

    def get_control_by_id(self, control_id):
        """Return the dictionary in an array of dictionaries with a key matching a value"""
        search_array = self.get_controls_all()
        search_key = "id"
        search_value = control_id
        result_dict = next(
            (sub for sub in search_array if sub[search_key] == search_value), None
        )
        return result_dict

    def get_control_property_by_name(self, control, property_name):
        """Return value of a property of a control by name of property"""
        if control is None:
            return None
        prop = self.find_dict_by_value(control["properties"], "name", property_name)
        if prop is None:
            return None
        return prop["value"]

    def get_control_part_by_name(self, control, part_name):
        """Return value of a part of a control by name of part"""
        if "parts" in control:
            part = self.find_dict_by_value(control["parts"], "name", part_name)
            return part
        else:
            return None

    def get_control_guidance_links(self, control):
        """Return the links in the guidance section of a control"""
        guidance = self.get_control_part_by_name(control, "guidance")
        if guidance and "links" in guidance:
            return guidance["links"]
        else:
            return []

    def get_guidance_related_links_by_value_in_href(self, control, value):
        """
        Return objects from 'rel': 'related' links with particular value found
        in the 'href' string
        """
        links = [
            link
            for link in self.get_control_guidance_links(control)
            if link["rel"] == "related" and value in link["href"]
        ]
        return links

    def get_guidance_related_links_text_by_value_in_href(self, control, value):
        """
        Return 'text' from rel': 'related' links with particular value found in
        the 'href' string
        """
        links_text = [
            link["text"]
            for link in self.get_control_guidance_links(control)
            if link["rel"] == "related" and value in link["href"]
        ]
        return links_text

    def get_control_parameter_label_by_id(self, control, param_id):
        """Return value of a parameter of a control by id of parameter"""
        param = self.find_dict_by_value(control["parameters"], "id", param_id)
        return param["label"]

    def get_control_prose_as_markdown(
        self, control_data, part_types={"statement"}, parameter_values=dict()
    ):
        status = self.get_control_property_by_name(control_data, "status")
        if status == "Withdrawn":
            return "Withdrawn"

        text = self.format_part_as_markdown(control_data, filter_name=part_types)

        text_params_replaced = self.substitute_parameter_text(
            control_data, text, parameter_values
        )

        return text_params_replaced

    def format_part_as_markdown(
        self,
        part,
        indentation_level=-1,
        indentation_string="    ",
        filter_name=None,
        hide_first_label=True,
    ):
        # Format part, which is either a control or a part, as Markdown.

        # First construct the prose text of this part. If there is a
        # label, put it at the start.

        md = ""

        # If this part has a label (i.e. "a."), get the label.
        label = ""
        if part is None:
            return ""
        label_property = self.find_dict_by_value(
            part.get("properties", []), "name", "label"
        )
        if label_property:
            label = label_property["value"] + " "
        # Hide first label to avoid showing control_id
        if indentation_level == -1 and hide_first_label:
            label = ""
        # Emit the label, if any.
        md += label

        # If it has a 'prose' key, then add that. The 'prose' is a string
        # that may contain Markdown formatting, so we don't touch it much
        # because we are supposed to produce markdown.
        #
        # OSCAL defines "markup-multiline" to use two escaped \n's to
        # denote paragraph boundaries, so we replace the literal "\n\n"
        # with two actual newline characters.
        if "prose" in part:
            prose = part["prose"]
            prose = prose.replace("\\n\\n", "\n\n")
            md += prose

        # If prose is multiple lines and if there is a label, then to be
        # valid Markdown, all lines after the first should be indented
        # the number of characters in the label (plus its space).
        if label:
            md = md.split("\n")
            for i in range(1, len(md)):
                md[i] = (" " * len(label)) + md[i]
            md = "\n".join(md)

        # Apply indentation. Each line of the prose should be indented
        # (not just the first line). Break the prose up into lines,
        # add the indentation at the start of each line, and then put
        # the lines back together again.
        # In Python, a string times an integer repeats it.
        md = "\n".join(
            [(indentation_level * indentation_string) + line for line in md.split("\n")]
        )

        # If there was any prose text, add a paragraph boundary.
        if md != "":
            md += "\n\n"

        # If it has sub-parts, then emit those.
        if "parts" in part:
            for part in part["parts"]:
                # If filter_name is given, filter out the parts that don't have
                # one of the givne names.
                if filter_name and part.get("name") not in filter_name:
                    continue

                # Append this part.
                md += self.format_part_as_markdown(
                    part,
                    indentation_string=indentation_string,
                    indentation_level=indentation_level + 1,
                )

        return md

    def substitute_parameter_text(self, control, text, parameter_values):
        # Fill in parameter_values with control parameter labels for any
        # parameters that are not specified.
        parameter_values = dict(
            parameter_values
        )  # clone so that we don't modify the caller's dict

        if control is None:
            return text
        if "parameters" not in control:
            return text

        for parameter in control["parameters"]:
            if parameter["id"] not in parameter_values:
                parameter_values[
                    parameter["id"]
                ] = f"[{parameter.get('label', parameter['id'])}]"

        for parameter_key, parameter_value in parameter_values.items():
            text = re.sub(
                r"{{ " + re.escape(parameter_key) + " }}", parameter_value, text
            )

        return text

    def get_flattened_control_as_dict(self, control):
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
                parameter_values=self.parameter_values,
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
                parameter_values=self.parameter_values,
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

    def get_flattened_controls_all_as_dict(self):
        """Return all controls as a simplified flattened Python dictionary indexed by control ids"""
        # Create an empty dictionary
        cl_all_dict = {}
        # Get all the controls
        for cl in self.get_controls_all():
            # Get flattened control and add to dictionary of controls
            cl_dict = self.get_flattened_control_as_dict(cl)
            cl_all_dict[cl_dict["id"]] = cl_dict
        return cl_all_dict

    def get_flattened_controls_all_as_dict_list(self):
        """Return all control dictionary in a nested Python list"""
        # Create an empty list
        cl_all_list = []
        # Get all the controls
        for cl in self.get_controls_all():
            # Get flattened control and add to list of controls
            cl_dict = self.get_flattened_control_as_dict(cl)
            cl_all_list.append(cl_dict)
        return cl_all_list

    def _cache_parameters_by_control(self):
        cache = defaultdict(list)
        if self.oscal:
            groups = self.oscal["groups"]
            for family in groups:
                for control in family["controls"]:
                    control_id = control["id"]
                    for parameter in control.get("parameters", []):
                        cache[control_id].append(parameter["id"])
        return dict(cache)

    def get_parameter_ids_for_control(self, control_id):
        return self.parameters_by_control.get(control_id, [])

    @property
    def catalog_title(self):
        metadata = self.oscal.get("metadata", {})
        return metadata.get("title", "")

