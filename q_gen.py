#
# Copyright 2026 Lavinia Egidi - UPO
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.

import json
import argparse
from pathlib import Path
from verify import controlla_json_friendly, verify_semantics, message
from gen_tools import *
import sys
import os


FILE_CONFIG = "config.json"
# defines inputs and options
def parse_args():
    parser = argparse.ArgumentParser(
        prog='q_gen',
        description='generates collections of questions in XML Moodle format from input JSON files')

    parser.add_argument("-i", "--input_file", help="input file", type=str)
    parser.add_argument("-s", "--source_directory", help="process all files in the specified source directory",
                        type=str)
    parser.add_argument("-o", "--out_dir", help="output directory", type=str)
    parser.add_argument("-j", "--join_dir", help="join all XML files from the specified join_directory (if there is already a join file, it is disregarded)", type=str)
    parser.add_argument("-c", "--config_file", help="use specified config_file as configuration file (default is config.json); the config_file must be in JSON format", type=str)
    parser.add_argument("-v", "--verify_json_file",
                        help="verify that the JSON input file is syntactically correct (useful after preparing new configuration files)",
                        type=str)
    return parser.parse_args()

def forallfiles(input_directory,complete_raccolta, extension):
    allfiles = []
    for filename in os.listdir(input_directory):
        if filename.endswith("."+extension) and not filename.startswith(complete_raccolta):
            allfiles.append(os.path.join(input_directory,filename))
    return allfiles

def verify_template_existence(messages,names):
    for temp_name in names.values():
        if not os.path.exists(temp_name):
            message(messages,"ERROR_NOTFOUND",{"path":temp_name})

def join_collections(messages, dir_da_concatenare, nomifile):

    da_concatenare = forallfiles(dir_da_concatenare, nomifile["collections_concat"], "xml")
    if len(da_concatenare) == 0:
        message(messages,"ERROR_NOFILES_TYPE",{"dir":dir_da_concatenare,"file_type":"XML"})

    message(messages,"INFO_concat",{})

    with open( nomifile["template_collection"], 'r') as shellfile:
        shell_lines = shellfile.readlines()

    raccolta_completa = shell_lines[:2]

    for nomefileraccolta in da_concatenare:
        message(messages,"MSG_tab",{"text":nomefileraccolta})

        # Apri il file originale in lettura e quello nuovo in scrittura
        with open(nomefileraccolta, "r", encoding="utf-8") as raccolta:
            righe = raccolta.readlines()

        # Seleziona dalla terza riga (indice 2) fino alla penultima (indice -1 escluso)
        contenuto_raccolta = righe[2:-1]

        raccolta_completa = raccolta_completa + ["\n"] + contenuto_raccolta

    raccolta_completa = raccolta_completa + shell_lines[-1:]
    concat_file = os.path.join(dir_da_concatenare, nomifile["collections_concat"]+".xml")
    with open(concat_file, "w", encoding="utf-8") as file_raccolta_completa:
        file_raccolta_completa.writelines(raccolta_completa)

    message(messages,"INFO_out_collection",{"filename":concat_file})
    sys.exit(0)

def main():
    print("\n")
    print("************************************************************")
    print("*******                   q_gen                   **********")
    print("*******              version 2/10/2026            **********")
    print("************************************************************")
    print("\n")

    args = parse_args()

    config_file = FILE_CONFIG
    if not args.config_file is None:
        config_file = args.config_file
    if not os.path.exists(config_file):
        print(f"File {config_file} doesn't exist")
    elif not Path.is_file(config_file):
        print(f"{config_file} is not a file: after -c, specify a JSON file")

    with open(config_file, 'r') as file_db:
        cfg = json.load(file_db)

    nomifile = cfg["filenames"]
    template_files = {}
    for key, file_name in cfg["templates"].items():
        if key != "template_dir":
            template_files[key] = os.path.join(cfg["templates"]["template_dir"],cfg["templates"][key]+".xml")
    nomifile.update(template_files)

    messages = cfg["messages"]["infos"]|cfg["messages"]["errors"]|cfg["messages"]["warnings"]

    if not args.join_dir is None:
        tbc_dir = args.join_dir
        message(messages,"NFO_CONCAT",{"dir":tbc_dir})
        if not os.path.exists(tbc_dir):
            message(messages,"ERROR_NOTFOUND",{"path":tbc_dir})
        elif not Path.is_dir(tbc_dir):
            message(messages,"ERROR_NOTDIR",{"path":tbc_dir,"opt":"-j"})
        join_collections(messages, tbc_dir, nomifile)

    if not args.verify_json_file is None:
        if not os.path.exists(args.verify_json_file):
            message(messages,"ERROR_NOTFOUND",{"path":args.verify_json_file})
        elif not Path.is_dir(args.verify_json_file):
            message(messages,"ERROR_NOTFILE",{"path":args.verify_json_file,"opt":"-v"})
        else:
            controlla_json_friendly(messages,args.verify_json_file)
            exit(0)

    verify_template_existence(messages,template_files)

    lab = cfg["key_names"]
    daeseguire = []
    input_directory = ""
    all = False

    if not args.out_dir is None:
        if Path.exists(args.out_dir) and not Path.is_dir(args.out_dir):
            message(messages,"ERROR_NOTDIR",{"path":args.out_dir,"opt":"-o"})
        nomifile["out_dir"] = args.out_dir
    if not args.input_file is None:
        if not Path.exists(args.input_file):
            message(messages,"ERROR_NOTFOUND",{"path":args.input_file})
        elif not Path.is_file(args.input_file):
            message(messages,"ERROR_NOTFILE",{"path":args.input_file,"opt":"-i"})
        daeseguire = [args.input_file]

    elif not args.source_directory is None:
        all = True
        input_directory = args.source_directory
    elif not  cfg["exec"]:
        daeseguire.append(input(cfg["INFO_insert_file_name"]))
    elif "ALL" in cfg["exec"]:
        daeseguire = cfg['database']
    else:
        daeseguire = cfg['exec']

    if all:
        if not input_directory:
            input_directory = nomifile["source_dir"]
        daeseguire = forallfiles(input_directory,nomifile["collections_concat"],"json")

    if len(daeseguire) == 0:
        message(messages,"WARNING_no_files",{})
    for nome in daeseguire:
        barename = Path(nome).stem
        input_path = Path(nome).parent
        nomefilerisposte = barename + ".json"
        if nomifile["sourcefile_prefix"] and nomifile["sourcefile_prefix"] in barename:
            barename = barename.split(nomifile["sourcefile_prefix"])[1]
        elif nomifile["sourcefile_prefix"] and len(Path(nome).parts) == 1 and not nomifile["sourcefile_prefix"] in barename:
            nomefilerisposte = nomifile["sourcefile_prefix"] + nomefilerisposte
        if len(Path(nome).parts) == 1:
            input_path = nomifile["source_dir"]

        nomefilerisposte = os.path.join(input_path,nomefilerisposte)
        message(messages,"INFO_PROCESSING",{"path":nomefilerisposte})
        if not os.path.exists(nomefilerisposte):
            message(messages,"ERROR_NOTFOUND",{"path":nomefilerisposte})

        risposte = controlla_json_friendly(messages,nomefilerisposte)

        verify_semantics(messages,risposte, cfg, lab)
        message(messages,"OK_VERIFIED",{"filename":nomefilerisposte})

        # each statement can be a dictionary or it can be simple: it will be converted here to dictionary
        risposte[lab["statements"]] = convert_to_dictionary(risposte, lab)

        template = genera_template(risposte, nomifile, lab)

        # in risposte[COMPLETE_STATEMENTS] the statements are in the correct moodle format, so the generation of combinations is no longer mixed with the preparation of the moodle syntax
        risposte[COMPLETE_STATEMENTS] = {}
        complete_answers(risposte, nomifile,lab)

        questions, numero_totale = prepare_questions(risposte, template,lab)
        message(messages,"MSG_total_no_of_q",{"number":numero_totale})
        with open(nomifile["template_collection"], 'r') as shellfile:
            shell = shellfile.read()
        template = shell.replace("__PHSINGOLEDOMANDE", questions).replace("__PHCATEGORY", risposte[lab["category"]])

        if not os.path.exists(nomifile["out_dir"]):
            os.makedirs(nomifile["out_dir"])
            message(messages,"INFO_dir_created",{"dir":nomifile["out_dir"]})

        nomefileraccolta = os.path.join(nomifile["out_dir"],nomifile["outfile_prefix"] + barename + ".xml")
        message(messages,"INFO_out_collection",{"filename":nomefileraccolta})
        with open(nomefileraccolta, 'w', encoding='utf-8') as file:
            file.write(template)

    return 0

if __name__ == "__main__":
    sys.exit(main())


