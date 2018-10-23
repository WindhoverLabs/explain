"""
 
    Copyright (c) 2018 Windhover Labs, L.L.C. All rights reserved.
 
  Redistribution and use in source and binary forms, with or without
  modification, are permitted provided that the following conditions
  are met:
 
  1. Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.
  2. Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in
     the documentation and/or other materials provided with the
     distribution.
  3. Neither the name Windhover Labs nor the names of its contributors 
     may be used to endorse or promote products derived from this software
     without specific prior written permission.
 
  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
  FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
  COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
  INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
  BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
  OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
  AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
  ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
  POSSIBILITY OF SUCH DAMAGE.

"""

""" 
The following are utility functions for taking the explain generated symbols 
JSON and converting it ot the format expected by the serialization autogenerator
"""

from collections import OrderedDict
from copy import deepcopy
import json
from os.path import join

def setup_serialization_dict(apps):
    """ Generate the base dictionary that will be populated by this 
    script with expected fields """
    base_dict = {}
    base_dict["Airliner"] = {}
    base_dict["autogen_version"] = ""
    base_dict["Airliner"]["apps"] = {}

    for app in apps:
        base_dict["Airliner"]["apps"][app] = {}
        base_dict["Airliner"]["apps"][app]["app_name"] = app
        base_dict["Airliner"]["apps"][app]["app_ops_name"] = app
        base_dict["Airliner"]["apps"][app]["proto_msgs"] = {}
        base_dict["Airliner"]["apps"][app]["operations"] = {}

    return base_dict
    
def get_pb_name(sym_name):
    """ Get the pb name for this symbol """
    return sym_name + "_pb"

def get_pb_type(sym):
    """ Given a symbol, return the protobuf type equivalent """
    primitives = ["int", "float", "char", "double"]
    type_map = {
        "uint8":   "uint32",
        "uint16":  "uint32",
        "uint32":  "uint32",
        "uint64":  "uint64",
        "int8":    "int32",
        "int16":   "int32",
        "int32":   "int32",
        "int64":   "int64",
        "char":    "string",
        "boolean": "bool",
        "float":   "float",
        "double":   "double",
    }
    global explain_dict
    
    if sym["real_type"] in type_map:
        return type_map[sym["real_type"]]
    if is_enum(sym["real_type"]):
        return "uint32"
    if sym["real_type"] in explain_dict["symbols"]:
        if "real_type" in explain_dict["symbols"][sym["real_type"]] and explain_dict["symbols"][sym["real_type"]]["real_type"] in type_map:
            #print explain_dict["symbols"][sym["real_type"]]["real_type"]
            return type_map[explain_dict["symbols"][sym["real_type"]]["real_type"]]
        if "fields" in explain_dict["symbols"][sym["real_type"]]:
            if len(explain_dict["symbols"][sym["real_type"]]["fields"]) == 1:
                try:
                    if "real_type" in explain_dict["symbols"][sym["real_type"]]["fields"][0]:
                        if "*" in explain_dict["symbols"][sym["real_type"]]["fields"][0]["real_type"]:
                            return "uint32"
                except KeyError as e:
                    key = next(iter(explain_dict["symbols"][sym["real_type"]]["fields"]))
                    if "airliner_type" in explain_dict["symbols"][sym["real_type"]]["fields"][key]:
                        # Found previously fixed type
                        return explain_dict["symbols"][sym["real_type"]]["fields"][key]["airliner_type"]
                    return "NULL" 
    if "base_type" in sym:
        base = sym["base_type"].split(' ')[-1]
        if base in primitives:
            if base == "int":
                unsigned = "unsigned" in sym["base_type"]
                if sym["bit_size"] <= 32:
                    return "uint32" if unsigned else "int32"
                else:
                    return "uint64" if unsigned else "int64"
            else: # TODO this may need to be smarter
                return type_map[base]
                
        
    return get_pb_name(sym["real_type"])

def fix_fields(sym):
    """ Iterate over all fields in a symbol with a depth first search
    to convert to expected format of serialization autogenerator """
    
    if "fields" not in sym:
        return sym

    # Iterate over all fields in this symbol
    fields = {}
    for field in sym["fields"]:
        name = field["name"]

        # Check if this field is another symbol
        if "fields" in field:
            # Recur into lowest level of nested fields and fix bottom up
            field = fix_fields(field)

        # Set new dict key equal to this field
        fields[name] = field

        # Set name for this field
        fields[name]["airliner_name"] = name
        
        # Remove unused keys from field
        del fields[name]["name"]            
        if "type" in fields[name]:
            if "base_type" in fields[name]["type"]:
                fields[name]["base_type"] = fields[name]["type"]["base_type"]
            del fields[name]["type"]
        
        # Set proper airliner and ptotobuf types for this field
        if "real_type" in fields[name]:
            if fields[name]["real_type"][0] == '*':
                fields[name]["airliner_type"] = "uint32"
                fields[name]["pb_type"] = "uint32"
            else:
                fields[name]["airliner_type"] = fields[name]["real_type"]
                fields[name]["pb_type"] = get_pb_type(fields[name])
            del fields[name]["real_type"]

        # Check base type if this is a pointer
        if "base_type" in fields[name]:
            if fields[name]["base_type"][0] == '*':
                fields[name]["airliner_type"] = "uint32"
                fields[name]["pb_type"] = "uint32"
            del fields[name]["base_type"]
        
        # Set array length
        if "array" in fields[name]:
            fields[name]["array_length"] = fields[name]["count"]
            del fields[name]["count"]
            del fields[name]["array"]
            # Don't set a string with fixed length to an array type
            if fields[name]["pb_type"] == "string":
                fields[name]["pb_field_rule"] = "required"
            else:
                fields[name]["pb_field_rule"] = "repeated"
        else:
            fields[name]["array_length"] = 0
            fields[name]["pb_field_rule"] = "required"
        
    sym["fields"] = fields
    return sym
        
def fix_required(symbol):
    """ Iterate over all fields of a symbol and correctly add any nested symbols to the
    appropriate required_pb_msgs of given symbol. Performs a breadth first search on a symbol """
    
    if "fields" not in symbol:
        return {}
        
    def fix(sym, req_pb={}, parent=None):
        # Check if this is another symbol
        if "fields" not in sym:
            # If not we have reached a primitive and should just return our current req_pb dictionary
            return req_pb

        # Iterate over all fields in this symbol
        for field, data in sym["fields"].items():
            # Don't do anything to or recur into fields which are not other symbols
            if "fields" not in data:
                continue
            
            # Verify this is a valid symbol with types set
            if "airliner_type" in data and "pb_type" in data:
                sym_type = data["airliner_type"]
                pb_type = data["pb_type"]
            else:
                continue
            
            # Check if this is a pointer
            if sym_type == "uint32" or pb_type == "uint32":
                del data["fields"]
                continue
            
            # If parent is set we have already recurred into a nested symbol
            if parent:
                # Check if the current symbol has already been added to the parent's required types dictionary
                if pb_type in parent["required_pb_msgs"]:
                    # This symbol has been added so we just need to add this symbol to the parent field map. 
                    # We need the value to be populated because jinja struggles with arrays, so we use a dictionary instead.
                    parent["required_pb_msgs"][pb_type]["parent_field"][field] = 0
                else:            
                    # Add the required pb message
                    parent["required_pb_msgs"][pb_type] = {}
                    parent["required_pb_msgs"][pb_type]["airliner_msg"] = sym_type
                    parent["required_pb_msgs"][pb_type]["parent_field"] = {field:0}
                    parent["required_pb_msgs"][pb_type]["fields"] = data["fields"]
                    parent["required_pb_msgs"][pb_type]["required_pb_msgs"] = {}
                    
                # Recur into next level of nested fields and fix top down
                req_pb = fix(data, req_pb, parent["required_pb_msgs"][pb_type])
                
            else:
                # If this required pb message already exists, add our current field to the parent field dict in req_pb
                if req_pb and pb_type in req_pb:
                    # This symbol has been added so we just need to add this symbol to the parent field map. 
                    # We need the value to be populated because jinja struggles with arrays, so we use a dictionary instead.
                    req_pb[pb_type]["parent_field"][field] = 0
                else:
                    # Add required pb message
                    req_pb[pb_type] = {}
                    req_pb[pb_type]["airliner_msg"] = sym_type
                    req_pb[pb_type]["parent_field"] = {field:0}
                    req_pb[pb_type]["fields"] = data["fields"]
                    req_pb[pb_type]["required_pb_msgs"] = {}

                # Recur into next level of nested fields and fix top down
                req_pb = fix(data, req_pb, req_pb[pb_type])

            # Remove fields from struct field
            del data["fields"]
                
        return req_pb

    return fix(symbol, OrderedDict())

def setup_ops_names(sym):
    """ Iterate over all fields in a symbol with a depth first search
    to setup the operational names and field path of each accessible field """
    
    if "fields" not in sym:
        return {}

    global ops_names
    ops_names = {}
    
    def search(sym, parent):
        global ops_names
        # Iterate over all fields in this symbol
        for field in sym["fields"]:
            # Set parent name appropriately
            name = field["name"]
            field_path = parent + "." + name if parent else name
            
            # Check if this field is another symbol
            if "fields" in field:
                # Recur into lowest level of nested fields and fix bottom up
                field = search(field, field_path)
                # If this field is a symbol we don't want it to be an ops name
                continue

            # Set new dict key equal to this field
            ops_names[field_path] = {"field_path": field_path}

    search(sym, None)
    
    #print ops_names
    
    return ops_names

def is_enum(sym):
    """ Check if the passed symbol is an enumeration so its protobuf type can 
    be set appropriately. """
    
    # TODO this should probably be smarter
    global explain_dict
    if explain_dict and sym in explain_dict["symbols"]:
        if explain_dict["symbols"][sym]["bit_size"] == 32 and "fields" not in explain_dict["symbols"][sym]:
            return True
    return False

def valid_symbol(sym, data):
    """ Check if the passes symbol is a valid symbol """
    if "fields" not in data:
        return False
    elif "_pb" in sym:
        return False

    return True

def convert(explain, out_dir):
    """ Given an explain symbol json, perform all conversion operations for the
    serialization autogenerator """
    global explain_dict
    explain_dict = explain
    # Parse app names
    apps = [app.split('.')[0] for app in explain_dict["files"]]
    apps.append("PX4")
    apps.append("CFE")
    serial_input = setup_serialization_dict(apps)
    serial_input["Airliner"]["little_endian"] = explain["little_endian"]

    # Reformat data into expected form
    for symbol, data in explain_dict["symbols"].items():
        # Skip empty struct definitions - we don't care about those here
        if not valid_symbol(symbol, data):
            continue
        
        # Lookup app name for this message so it can be placed correctly. TODO find a better way - this could drop messages
        app_name = symbol.split("_")[0]
        if app_name not in apps:
            continue

        # Do ops name parsing first. Fix fields modifys data format    
        operational_names = setup_ops_names(data)

        # Fix fields so key is message name
        serial_input["Airliner"]["apps"][app_name]["proto_msgs"][symbol] = fix_fields(data)
        
        # Remove unused keys
        if "type" in serial_input["Airliner"]["apps"][app_name]["proto_msgs"][symbol]:
            del serial_input["Airliner"]["apps"][app_name]["proto_msgs"][symbol]["type"]
        if "base_type" in serial_input["Airliner"]["apps"][app_name]["proto_msgs"][symbol]:
            del serial_input["Airliner"]["apps"][app_name]["proto_msgs"][symbol]["base_type"]
        if "real_type" in serial_input["Airliner"]["apps"][app_name]["proto_msgs"][symbol]:
            del serial_input["Airliner"]["apps"][app_name]["proto_msgs"][symbol]["real_type"]

        # Set name of protobuf message correctly
        serial_input["Airliner"]["apps"][app_name]["proto_msgs"][symbol]["proto_msg"] = get_pb_name(symbol)
        
        # Set required protobuf messages field according to expected format
        serial_input["Airliner"]["apps"][app_name]["proto_msgs"][symbol]["required_pb_msgs"] = fix_required(data)

        # Add expected fields for pyliner - TODO: These need to be manually populated right now
        serial_input["Airliner"]["apps"][app_name]["proto_msgs"][symbol]["operational_names"] = operational_names
        serial_input["Airliner"]["apps"][app_name]["operations"][symbol] = {}
        serial_input["Airliner"]["apps"][app_name]["operations"][symbol]["airliner_msg"] = symbol
        serial_input["Airliner"]["apps"][app_name]["operations"][symbol]["airliner_cc"] = -1
        serial_input["Airliner"]["apps"][app_name]["operations"][symbol]["airliner_mid"] = ""
           
    with open(join(out_dir, "cookiecutter.json"), "w") as cc:
        output = serial_input#OrderedDict(sorted(serial_input.items(), key = lambda x: serial_input['Airliner']['apps'][x]))
        json.dump(output, cc, indent=4)

    # Generate a copy of the cookiecutter but only with field ops names
    with open(join(out_dir, "pyliner_ops_names.json"), "w") as cc:
        delete_apps = []
        output = deepcopy(serial_input)
        for app, app_data in output["Airliner"]["apps"].items():
            del app_data["app_name"]
            del app_data["operations"]
            if app_data["proto_msgs"] == {}:
                delete_apps.append(app)
                continue
            for symbol, sym_data in app_data["proto_msgs"].items():
                del sym_data["bit_size"]
                del sym_data["fields"]
                del sym_data["proto_msg"]
                del sym_data["required_pb_msgs"]
                
        for app in delete_apps:
            del output["Airliner"]["apps"][app]

        json.dump(output, cc, indent=4)

    # Generate a copy of the cookiecutter but only with app operations
    with open(join(out_dir, "pyliner_msgs.json"), "w") as cc:
        delete_apps = []
        output = deepcopy(serial_input)
        for app, app_data in output["Airliner"]["apps"].items():
            del app_data["app_name"]
            del app_data["app_ops_name"]
            if app_data["proto_msgs"] == {}:
                delete_apps.append(app)
                continue
            del app_data["proto_msgs"]

        for app in delete_apps:
            del output["Airliner"]["apps"][app]
        json.dump(output, cc, indent=4)



   
