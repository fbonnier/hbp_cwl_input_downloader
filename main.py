import os
import argparse
import json as json
import warnings

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
def build_json_file (id, repos, inputs, outputs, runscript):
    json_content = {
        "id" : id,
        "source" : repos,
        "inputs": inputs,
        "results": outputs,
        "run": runscript
    }


def get_cwl_json_kg3 (token=None, id=None, run=None):

    # Fairgraph
    client = KGClient(token)
    print("Fairgraph Token ok")
    try:
        model_version = ModelVersion.from_id(id, client)
        model_version.show()
        print("Model Version ok")

        # Get repo location
        instance_repo = model_version.repository
        if not instance_repo:
            raise Exception ("Instance repository does not exists")
        print ("Repo :")
        print (instance_repo)
        print("\n")
        instance_repo = model_version.repository.resolve(client)
        print ("Repo solved :")
        print (instance_repo)
        print("\n")

        # Get inputs
        #       !! No exception raised if no inputs
        #       !! Warning message is shown instead
        instance_inputs = model_version.input_data
        if not instance_inputs:
            warnings.warn("No input data for this Instance ... Continue")
        else:
            print ("Inputs :")
            print (instance_inputs)
            print("\n")

        # Get Outputs
        # Decision: What to do with no output expected ?
        # ! Exception raised
        instance_outputs = model_version.output_data
        if not instance_outputs:
            warnings.warn("No output data to compare for this Instance ... Continue")
        else:
            print ("Outputs :")
            print (instance_outputs)
            print("\n")

        # Get Run instructions,
        # by default the run instruction is set according to parameter $run
        # TODO:
        # - Add run instruction Download
        if not run:
            raise Exception ("No run instruction specified for this Instance")
        instance_run = run
        print ("Run Instruction :")
        print (instance_run)
        print("\n")

        # Build JSON File that contains all important informations
        build_json_file (id, instance_repo, instance_inputs, instance_outputs, instance_run)

    except Exception as e:
        print ("Error:")
        print (e)
        exit (1)
    except:
        print ("Error: Unknown Error")
        exit (1)

def get_cwl_json_kg2 (token, id):
    # Log to EBRAINS KG_v2
    catalog = ModelCatalog(token=str(token))

    try:
        # Get JSON File
        instance = catalog.get_model_instance(instance_id=str(id))
        print ("Catalog Instance")
        print (instance)
        json_content = json.loads(instance["parameters"])

        if type(instance["source"]) is list:
            json_content["source"] = instance["source"]
        else:
            json_content["source"] = [instance["source"]]

        # A list of run instructions is expected
        if type(json_content["run"]) is not list:
            json_content["run"] = [json_content["run"]]

        # A list of inputs is expected
        if type(json_content["inputs"]) is not list:
            json_content["inputs"] = [json_content["inputs"]]

        # A list of outputs is expected
        if type(json_content["results"]) is not list:
            json_content["results"] = [json_content["results"]]

        # A list of additional pip install is expected
        if type(json_content["pip_installs"]) is not list:
            json_content["pip_installs"] = [json_content["pip_installs"]]

        # write in file
        with open("./input.json", "w") as f:
            json.dump(json_content, f)


        print ("\nJSON Content:")
        print (json_content)

    except:
        # print (e)
        print ("Error inconnue")
        exit (1)

    print ("\nSuccess:  File created in \"./input.json\"")



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
