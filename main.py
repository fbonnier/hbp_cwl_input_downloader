import os
import argparse
import json as json

from hbp_validation_framework import ModelCatalog

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

    args = parser.parse_args()

    if args.token:
        if args.id:
            get_cwl_json_kg2(token=args.token[0], id=args.id[0])
        else:
            print ("Error: Instance ID not recognized")
            exit (1)
    else:
        print ("Error: Authentification failed")
        exit (1)

    exit(0)
