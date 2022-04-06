import os
import argparse
import json as json

# Fairgraph
from fairgraph import KGClient
import fairgraph.openminds.core as omcore
from fairgraph.openminds.core.products.model_version import ModelVersion

from hbp_validation_framework import ModelCatalog

# Source server from which the ALREADY KG-v3 instances are downloaded
# Default is Official KG-v3 server
SOURCE_SERVER = "https://core.kg.ebrains.eu"
# SOURCE_SERVER = "https://kg.ebrains.eu/api/instances/"

# KG-v3, KG-Core Python Interface
from kg_core.oauth import SimpleToken
from kg_core.kg import KGv3
from kg_core.models import Stage
from kg_core.models import Pagination


def get_cwl_json_kg3 (token=None, id=None):
    # token_handler = SimpleToken(token)
    # print("Simple Token OK")
    # catalog = KGv3(host=SOURCE_SERVER, token_handler=token_handler)
    # print("Catalog OK")
    # instance_metadata = catalog.get_instance(stage=Stage.RELEASED, instance_id=id).data()
    # print ("KGV3 instance:\n")
    # print (instance_metadata)
    # print ("\n\n")

    # Fairgraph
    client = KGClient(token=token)
    print("Fairgraph Token ok")
    print(omcore.list_kg_classes())
    print("List kg classes ok")
    # model_version = ModelVersion.list(client, id=id, space="model")
    model_version = ModelVersion.list(client, scope='released')


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

    parser.add_argument("--kg", type=int, metavar="KG version", nargs=1, dest="kg", default=3,\
    help="Version of Knowledge Graph to use. Should be 2 or 3")

    args = parser.parse_args()

    token = args.token[0]
    id = args.id[0]
    kg = args.kg[0]

    # print ("Token:" + str(token) + " " + str(type(token)))
    # print ("Id:" + str(id) + " " + str(type(id)))
    # print ("KGv:" + str(kg) + " " + str(type(kg)))


    if token:
        if id:
            if kg == 2:
                get_cwl_json_kg2(token=token, id=id)
            elif kg == 3:
                get_cwl_json_kg3(token=token, id=id)
            else:
                print("Error: KG Version not recognized")
                exit (1)
        else:
            print ("Error: Instance ID not recognized")
            exit (1)
    else:
        print ("Error: Authentification failed")
        exit (1)

    exit(0)
