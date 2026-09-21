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
from verify import controlla_json_friendly, verifica, error_message, warning_message
from gen_tools import *
import sys
import os

FILE_CONFIG = "config.json"
# defines inputs and options
def parse_args():
    parser = argparse.ArgumentParser(
        prog='q_gen',
        description='genera domande in formato Moodle XML da file JSON in input')

    parser.add_argument("-i", "--input_file", help="file in input", type=str)
    parser.add_argument("-s", "--source_directory", help="elaborare tutti i file nella cartella source_directory",
                        type=str)
    parser.add_argument("-o", "--out_dir", help="output directory", type=str)
    parser.add_argument("-j", "--join_dir", help="concatena i file specificati nella cartella join_directory", type=str)
    parser.add_argument("-c", "--config_file", help="usa config_file come file di configurazione (default config.json); config_file deve essere in formato JSON", type=str)
    return parser.parse_args()

def forallfiles(input_directory,complete_quiz, extension):
    allfiles = []
    for filename in os.listdir(input_directory):
        if filename.endswith("."+extension) and not filename.startswith(complete_quiz):
            allfiles.append(os.path.join(input_directory,filename))
    return allfiles

def verify_template_existence(names):
    for temp_name in names.values():
        if not os.path.exists(temp_name):
            error_message(f"Errore! Non esiste il template {temp_name}. Devono esistere i template necessari.")

def concatena(cfg,dir_da_concatenare,nomifile):

    da_concatenare = forallfiles(dir_da_concatenare, nomifile["collections_concat"], "xml")
    if len(da_concatenare) == 0:
        error_message(f"Nella cartella {dir_da_concatenare} non ci sono quiz")

    print(f"➡️ Concatenazione dei quiz:")

    with open( nomifile["template_quiz"], 'r') as shellfile:
        shell_lines = shellfile.readlines()

    quiz_completo = shell_lines[:2]

    for nomefilequiz in da_concatenare:
        print(f"\t{nomefilequiz}")

        # Apri il file originale in lettura e quello nuovo in scrittura
        with open(nomefilequiz, "r", encoding="utf-8") as quiz:
            righe = quiz.readlines()

        # Seleziona dalla terza riga (indice 2) fino alla penultima (indice -1 escluso)
        contenuto_quiz = righe[2:-1]

        quiz_completo = quiz_completo + ["\n"] + contenuto_quiz

    quiz_completo = quiz_completo + shell_lines[-1:]
    concat_file = os.path.join(dir_da_concatenare, nomifile["collections_concat"]+".xml")
    with open(concat_file, "w", encoding="utf-8") as file_quiz_completo:
        file_quiz_completo.writelines(quiz_completo)

    print(f"\n➡️ Output salvato in {concat_file}")
    sys.exit(0)

def main():
    print("\n")
    print("************************************************************")
    print("*******                   q_gen                   **********")
    print("*******     generazione di domande per Moodle     **********")
    print("************************************************************")
    print("\n")

    args = parse_args()

    config_file = FILE_CONFIG
    if not args.config_file is None:
        config_file = args.config_file
    if not os.path.exists(config_file):
        error_message(f"Errore! Non esiste il file {config_file}")
    elif not Path.is_file(config_file):
        error_message(f"Errore! {config_file} non è un file: dopo l'opzione -c, specificare un file JSON")


    print("File di configurazione:",config_file)
    cfg = controlla_json_friendly(config_file)
    with open(config_file, 'r') as file_db:
        cfg = json.load(file_db)

    nomifile = cfg["filenames"]
    template_files = {}
    for key, file_name in cfg["templates"].items():
        if key != "template_dir":
            template_files[key] = os.path.join(cfg["templates"]["template_dir"],cfg["templates"][key]+".xml")
    nomifile.update(template_files)

    if not args.join_dir is None:
        tbc_dir = args.join_dir
        warning_message(f"È stata richiesta la concatenazione dei file nella cartella {tbc_dir}\n")
        if not os.path.exists(tbc_dir):
            error_message(f"Errore! Non esiste la cartella {tbc_dir}")
        elif not Path.is_dir(tbc_dir):
            error_message(f"Errore! {tbc_dir} non è una cartella: dopo l'opzione -j, specificare una cartella")
        concatena(cfg, tbc_dir, nomifile)

    verify_template_existence(template_files)

    lab = {}
    for key in cfg["necessary_input_fields"]:
        lab.update(cfg["necessary_input_fields"][key])
    for key in cfg["meaningful_options"]:
        lab.update(cfg["meaningful_options"][key])

    daeseguire = []
    input_directory = ""
    all = False

    if not args.out_dir is None:
        if Path.exists(args.out_dir) and not Path.is_dir(args.out_dir):
            error_message(f"Errore! {args.out_dir} è un file: dopo l'opzione -o, specificare una cartella")
        nomifile["out_dir"] = args.out_dir
    if not args.input_file is None:
        if not Path.exists(args.input_file):
            error_message(f"Errore! Il file {args.input_file} non esiste")
        elif not Path.is_file(args.input_file):
            error_message(f"Errore! {args.input_file} non è un file: dopo l'opzione -i specificare il nome di un file")
        daeseguire = [args.input_file]

    elif not args.source_directory is None:
        all = True
        input_directory = args.source_directory
    elif not  cfg["exec"]:
        daeseguire.append(input("Inserisci il nome del file: "))
    elif "ALL" in cfg["exec"]:
        daeseguire = cfg['database']
    else:
        daeseguire = cfg['exec']

    if all:
        if not input_directory:
            input_directory = nomifile["source_dir"]
        daeseguire = forallfiles(input_directory,nomifile["collections_concat"],"json")

    if len(daeseguire) == 0:
        warning_message(f"Non sono stati specificati file JSON da elaborare")
    for nome in daeseguire:
        print("nome:",nome)
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
        print(f"\n\n➡️ Elaborazione di {nomefilerisposte}")
        if not os.path.exists(nomefilerisposte):
            error_message(f"Errore! Non esiste il file {nomefilerisposte}")

        risposte = controlla_json_friendly(nomefilerisposte)

        verifica(risposte, cfg, lab)
        print("✅ Il file", nomefilerisposte, "contiene i campi previsti e, per quanto verificato, è logicamente corretto")

        # each statement can be a dictionary or it can be simple: it will be converted here to dictionary
        risposte[lab["statements"]] = convert_to_dictionary(risposte, lab)

        template = genera_template(risposte, nomifile, lab)

        # in risposte[COMPLETE_STATEMENTS] the statements are in the correct moodle format, so the generation of combinations is no longer mixed with the preparation of the moodle syntax
        risposte[COMPLETE_STATEMENTS] = {}
        complete_answers(risposte, nomifile,lab)
        # for group in risposte[COMPLETE_STATEMENTS]:
        #     print(f"il gruppo {group} contiene {len(risposte[COMPLETE_STATEMENTS][group])} frasi")

        questions, numero_totale = prepare_questions(risposte, template,lab)
        print("numero totale domande generate", numero_totale)
        with open(nomifile["template_quiz"], 'r') as shellfile:
            shell = shellfile.read()
        template = shell.replace("__PHSINGOLEDOMANDE", questions).replace("__PHCATEGORY", risposte[lab["category"]])

        if not os.path.exists(nomifile["out_dir"]):
            print(f"Creata la cartella {nomifile['out_dir']}")
            os.makedirs(nomifile["out_dir"])

        nomefilequiz = os.path.join(nomifile["out_dir"],nomifile["outfile_prefix"] + barename + ".xml")
        print(f"Il quiz è nel file {nomefilequiz}")
        with open(nomefilequiz, 'w', encoding='utf-8') as file:
            file.write(template)

    return 0

if __name__ == "__main__":
    # sys.argv contiene gli argomenti passati da riga di comando.
    # sys.exit() per restituire un codice di stato al sistema operativo.
    sys.exit(main())
#         sys.exit(main(sys.argv[1:]))


