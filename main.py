import os
import argparse

from hbp_validation_framework import ModelCatalog

def download_cwl_json (token, id):
    # Log to EBRAINS KG_v2
    catalog = ModelCatalog(token=str(token))

    try:
        # Get JSON File
        instance = catalog.get_model_instance(instance_id=str(id))

        # write in file
        f = open("./input.json", "w")
        f.write(instance["parameters"])
        f.close()
        print (instance["parameters"], file=sys.stdout)

    except:
        # print (e)
        print ("Error inconnue", file=sys.stderr)
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
            download_cwl_json(token=args.token[0], id=args.id[0])
        else:
            print ("Error: Instance ID not recognized", file=sys.stderr)
            exit (1)
    else:
        print ("Error: Authentification failed", file=sys.stderr)
        exit (1)

    exit(0)
