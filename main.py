import os
import argparse
import json as json
import warnings
import hashlib

# Fairgraph
from fairgraph import KGClient
import fairgraph.openminds.core as omcore
from fairgraph.openminds.core import ModelVersion

from fairgraph.openminds.core import DatasetVersion
from fairgraph.openminds.controlledterms import Technique

from hbp_validation_framework import ModelCatalog

# Source server from which the ALREADY KG-v3 instances are downloaded
# Default is Official KG-v3 server
SOURCE_SERVER = "https://core.kg.ebrains.eu"
# SOURCE_SERVER = "https://kg.ebrains.eu/api/instances/"

report_default_values = {
    "id": None, # str, ID of the model
    "workdir": "./", # str, path of the working directory
    "workflow": {
        "run": {
            "url": None, # URL of the workflow instruction file to download
            "path": None}, # Absolute path of the workflow instruction file to download
        "data": {
            "url": None, # URL of the workflow data file to download
            "path": None}, # Absolute path of the workflow data file to download
        },
    "run": {
        "code": [], # URL and Path of the code to download and execute, IRI, Label and Homepage
        "pre-instruction": [], # array of known instructions: untar, compile, move inputs, ...
        "instruction": None, # str
        "inputs": [], # Should contain "url" and "path" of input files to download
        "outputs": [], # Should contain "url", "path" and "hash" of expected output files to download
        "environment": {
            "pip install": [], # additional PIP packages to install
            "module deps": [], # additional module packages to load
            "profiling configuration": []} # profiling configuration to add for profiling and tracing analysis
    
    }
    }

# KG-v3, KG-Core Python Interface
# from kg_core.oauth import SimpleToken
# from kg_core.kg import KGv3
# from kg_core.models import Stage
# from kg_core.models import Pagination


### Parameters ###
#*****************
# id: str
# repos: str
# inputs: array of dict {url: x, destination: y}
# outputs: array of str
# runscript: array of str
def build_json_file (id, workdir, workflow, repos, inputs, outputs, runscript, environment):
    json_content = { "Metadata": report_default_values}
    
    # Asserts
    assert (id != None)
    assert (repos != None)
    assert (runscript != None)
    
    # Get Model's ID
    json_content["Metadata"]["id"] = id

    # Get Workdir
    json_content["Metadata"]["workdir"] = workdir if workdir else report_default_values["workdir"]

    # Get Workflow
    # 1. Run file
    try:
        json_content["Metadata"]["workflow"]["run"]["url"] = workflow["run"]
    
    except:
        json_content["Metadata"]["workflow"]["run"]["url"] = report_default_values["workflow"]["run"]["url"]
    json_content["Metadata"]["workflow"]["run"]["path"] = json_content["Metadata"]["workdir"]

    # 2. Data file
    try:
        json_content["Metadata"]["workflow"]["data"]["url"] = workflow["data"]
    
    except:
        json_content["Metadata"]["workflow"]["data"]["url"] = report_default_values["workflow"]["data"]["url"]
    json_content["Metadata"]["workflow"]["data"]["path"] = json_content["Metadata"]["workdir"]

    # Get run instructions
    # 1. Code URL
    json_content["Metadata"]["run"]["code"] = repos

    # 3. Pre-instructions
    json_content["Metadata"]["run"]["pre-instruction"] = report_default_values["run"]["pre-instruction"]
    # 4. instruction
    json_content["Metadata"]["run"]["instruction"] = runscript if runscript else report_default_values["run"]["instruction"]
    # 5. Inputs
    json_content["Metadata"]["run"]["inputs"] = inputs if inputs else report_default_values["run"]["inputs"]
    # 6. Expected outputs
    json_content["Metadata"]["run"]["outputs"] = outputs if outputs else report_default_values["run"]["outputs"]
    # 6.1 Calculates hash of outputs
    for ioutput in json_content["Metadata"]["run"]["outputs"]:
        # Calculates hash
        ioutput["hash"] = str(hashlib.md5(ioutput["url"].encode()).hexdigest())
        # Calculates output path
        ioutput["path"] = str(str(json_content["Metadata"]["workdir"]) + "/ouputs/" +
        str(ioutput["hash"]))
        
    # 7. Environment configuration
    # 7.1 PIP installs
    try:
        json_content["Metadata"]["run"]["environment"]["pip install"] = environment["pip install"]
    except:
        json_content["Metadata"]["run"]["environment"]["pip install"] = report_default_values["run"]["environment"]["pip install"]

    # 7.2 Module loads
    try:
        json_content["Metadata"]["run"]["environment"]["module deps"] = environment["module deps"]
    except:
        json_content["Metadata"]["run"]["environment"]["module deps"] = report_default_values["run"]["environment"]["module deps"]
    # 7.3 Profiling conf
    try:
        json_content["Metadata"]["run"]["environment"]["profiling configuration"] = environment["profiling configuration"]
    except:
        json_content["Metadata"]["run"]["environment"]["profiling configuration"] = report_default_values["run"]["environment"]["profiling configuration"]

    return json_content
    


def get_cwl_json_kg3 (token=None, id=None, run=None):

    # Fairgraph
    client = KGClient(token)
    if not client:
        raise Exception ("Client is " + str(type(client)))
    print("Fairgraph Token ok")
    try:
        model_version = ModelVersion.from_id(id, client)

        if not model_version:
            raise Exception ("ModelVersion is None")
        model_version.show()
    except Exception as e:
        print (e)
        exit (1)
    
    try:
        # Get repo location
        instance_repo = []
        if not model_version.repository:
            raise Exception ("Instance repository does not exists")
        instance_repo.append (model_version.repository.resolve(client).iri.value)
        # instance_repo.append (model_version.repository.resolve(client).label.value)
        instance_repo.append (model_version.homepage.resolve(client).url.value)
        print ("Repos : " + str(instance_repo))
    except Exception as e:
        print (e)
        exit (1)

    try:
        # Get inputs
        #       !! No exception raised if no inputs
        #       !! Warning message is shown instead
        instance_inputs = model_version.input_data
        if not instance_inputs:
            warnings.warn("No input data for this Instance ... Continue")

        # Get Outputs
        # Decision: What to do with no output expected ?
        # ! Exception raised
        instance_outputs = model_version.output_data
        if not instance_outputs:
            warnings.warn("No output data to compare for this Instance ... Continue")

        # Get Run instructions,
        # by default the run instruction is set according to parameter $run
        # TODO:
        # - Add run instruction Download
        if not run:
            raise Exception ("No run instruction specified for this Instance")
        instance_run = run
    except Exception as e:
        print (e)
        exit (1)

    try:
        # Build JSON File that contains all important informations
        json_content = build_json_file (id=id, workflow={}, workdir="", repos=instance_repo, inputs = instance_inputs, outputs=instance_outputs, runscript=instance_run, environment={})
        with open("./report.json", "w") as f:
            json.dump(json_content, f, indent=4)

    except Exception as e:
        print (e)
        exit (1)

# def get_cwl_json_kg2 (token, id):
#     # Log to EBRAINS KG_v2
#     catalog = ModelCatalog(token=str(token))

#     try:
#         # Get JSON File
#         instance = catalog.get_model_instance(instance_id=str(id))
#         print ("Catalog Instance")
#         print (instance)
#         json_content = json.loads(instance["parameters"])

#         if type(instance["source"]) is list:
#             json_content["source"] = instance["source"]
#         else:
#             json_content["source"] = [instance["source"]]

#         # A list of run instructions is expected
#         if type(json_content["run"]) is not list:
#             json_content["run"] = [json_content["run"]]

#         # A list of inputs is expected
#         if type(json_content["inputs"]) is not list:
#             json_content["inputs"] = [json_content["inputs"]]

#         # A list of outputs is expected
#         if type(json_content["results"]) is not list:
#             json_content["results"] = [json_content["results"]]

#         # A list of additional pip install is expected
#         if type(json_content["pip_installs"]) is not list:
#             json_content["pip_installs"] = [json_content["pip_installs"]]

#         # write in file
#         with open("./input.json", "w") as f:
#             json.dump(json_content, f)


#         print ("\nJSON Content:")
#         print (json_content)

#     except:
#         # print (e)
#         print ("Error inconnue")
#         exit (1)

#     print ("\nSuccess:  File created in \"./input.json\"")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download input file for CWL workflow from an HBP Model Instance ID")

    parser.add_argument("--id", type=str, metavar="Model Instance ID", nargs=1, dest="id", default="",\
    help="ID of the Instance to download")

    parser.add_argument("--token", type=str, metavar="Authentification Token", nargs=1, dest="token", default="",\
    help="Authentification Token used to log to EBRAINS")

    # parser.add_argument("--kg", type=int, metavar="KG version", nargs=1, dest="kg", default=3,\
    # help="Version of Knowledge Graph to use. Should be 2 or 3")

    ## Run instruction can be specified in command line
    ## A single instruction (str) is checked as of now
    parser.add_argument("--run", type=str, metavar="Run instruction", nargs=1, dest="run", default="./run",\
    help="Running instruction to run the model instance")

    args = parser.parse_args()

    token = args.token[0]
    id = args.id[0]
    # kg = args.kg[0]
    run = args.run[0]

    # print ("Token:" + str(token) + " " + str(type(token)))
    # print ("Id:" + str(id) + " " + str(type(id)))
    # print ("KGv:" + str(kg) + " " + str(type(kg)))


    if token:
        if id:
            # if kg == 2:
            #     get_cwl_json_kg2(token=token, id=id)
            # elif kg == 3:
            get_cwl_json_kg3(token=token, id=id, run=run)
            # else:
            #     print("Error: KG Version not recognized")
            #     exit (1)
        else:
            print ("Error: Instance ID not recognized")
            exit (1)
    else:
        print ("Error: Authentification failed")
        exit (1)

    exit(0)
