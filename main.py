import os
import argparse
import json as json
import warnings
import hashlib
import re
import requests
import urllib.request

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
        "code": [], # URL, Filepath and Path of the code to download and execute, IRI, Label and Homepage
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

#------------------------------
### ModelDB models
#------------------------------

def is_modeldb_page (url_link: str) -> bool:
    
    if url_link.startswith("https://senselab.med.yale.edu/") or url_link.startswith("http://modeldb.science/") or url_link.startswith("http://modeldb.yale.edu/"):
        return True
    return False

def get_modeldb_download_link_from_page (modeldb_page_url: str)-> int: 
    
    modeldb_id = None

    try:
        modeldb_id = re.findall("\d+", modeldb_page_url)[0]
    except Exception as e:
        print ("Exception: get_modeldb_download_link_from_page")
        print (e)
        
    return get_modeldb_download_link_from_id (int(modeldb_id))

def get_modeldb_download_link_from_id (modeldb_id: int):
    
    return (str("http://modeldb.science/eavBinDown?o=" + str(modeldb_id)))
#------------------------------

#------------------------------
### Github models
#------------------------------

def is_github_page (url_link: str) -> bool:
    if url_link.startswith("https://github.com/"):
        return True
    return False

def is_github_release_page (url_link: str) -> bool:
    
    if "releases/tag/" in url_link:
        return True
    return False

def get_github_download_link_from_homepage (github_homepage_url: str) -> str:

    # Get zip from master branch, also works for main
    zip_url = github_homepage_url + "/archive/refs/heads/master.zip"

    # Test zip url
    # return zip direct link on success
    # return None on failure
    response = requests.get(zip_url, stream=True)
    if not response.ok:
        zip_url = None

    return zip_url


def get_github_download_link_from_release_page (github_release_url: str) -> str:
    
    zip_url = None

    # Check if url is link to release page
    if is_github_release_page(github_release_url):
        
        # Get zip URL from release page
        zip_url = github_release_url.replace("/releases/tag/", "/archive/refs/tags/")
        zip_url = zip_url + ".zip"
        
        # Test zip url
        # return zip direct link on success
        # return None on failure
        response = requests.get(zip_url, stream=True)
        if not response.ok:
            zip_url = None

    return zip_url

#------------------------------


### Parameters ###
#*****************
# id: str
# repos: array of str
# inputs: array of dict {url: x, destination: y}
# outputs: array of str
# runscript: array of str
def build_json_file (id:str , workdir:str, workflow, repos, inputs, outputs, runscript, environment):
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
    for icode in repos:
        code = {"url": None, "filepath": None, "path": None}
        # ModelDB ?
        if is_modeldb_page (icode):
            code["url"] = get_modeldb_download_link_from_page(icode)
            
        
        # GitHub repo ?
        elif is_github_page (icode):

            # GitHub release ?
            if is_github_release_page(icode):
                code["url"] = get_github_download_link_from_release_page(icode)


            # GitHub home page
            else:
                code["url"] = get_github_download_link_from_homepage(icode)

        else:
            code["url"] = icode
            
        response = urllib.request.urlopen(code["url"])
        if "Content-Disposition" in response.headers.keys():
            dhead = response.headers['Content-Disposition']
            code["filepath"] = json_content["Metadata"]["workdir"] + re.findall("filename=(.+)", dhead)[0]
        else:
            code["filepath"] = json_content["Metadata"]["workdir"] + code["url"].split("/")[-1]
        
        folder = code["filepath"].split("/")[-1]
        code["path"] = json_content["Metadata"]["workdir"] + "/" + folder.split(".")[0] + "/"

        json_content["Metadata"]["run"]["code"].append(code)

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
    try:
        model_version = ModelVersion.from_id(id, client)

        if not model_version:
            raise Exception ("ModelVersion is None")
        # model_version.show()
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
        if model_version.homepage:
            instance_repo.append (model_version.homepage.resolve(client).url.value)
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
        with open(str(json_content["Metadata"]["workdir"] + "/report.json"), "w") as f:
            json.dump(json_content, f, indent=4)

        if "report.json" in os.listdir(json_content["Metadata"]["workdir"]):
            print ("File created successfully")

    except Exception as e:
        print (e)
        exit (1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download input file for CWL workflow from an HBP Model Instance ID")

    parser.add_argument("--id", type=str, metavar="Model Instance ID", nargs=1, dest="id", default="",\
    help="ID of the Instance to download")

    parser.add_argument("--token", type=str, metavar="Authentification Token", nargs=1, dest="token", default="",\
    help="Authentification Token used to log to EBRAINS")

    ## Run instruction can be specified in command line
    ## A single instruction (str) is checked as of now
    parser.add_argument("--run", type=str, metavar="Run instruction", nargs=1, dest="run", default="./run",\
    help="Running instruction to run the model instance")

    args = parser.parse_args()

    token = args.token[0]
    id = args.id[0]
    run = args.run[0]

    if token:
        if id:
            get_cwl_json_kg3(token=token, id=id, run=run)
        else:
            print ("Error: Instance ID not recognized")
            exit (1)
    else:
        print ("Error: Authentification failed")
        exit (1)
    
    exit(0)
