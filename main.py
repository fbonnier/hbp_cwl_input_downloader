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
        json_content["source"] = [instance["source"]]
        print ("\n")
        print ("JSON Content")
        print (json_content)

        # write in file
        with open("./input.json", "w") as f:
            json.dump(json_content, f)

    except:
        # print (e)
        print ("Error inconnue")
        exit (1)



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
