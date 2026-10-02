#
# Copyright 2026 Lavinia Egidi - UPO
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.

import json
import sys
from string import Template

def message(message_templates,msg,parameters):
    template = Template(message_templates[msg])
    tbp = template.safe_substitute(parameters)

    if msg.startswith("ERROR"):
        print("❌", tbp)
        sys.exit(1)
    elif msg.startswith("WARNING"):
        print("⚠️", tbp)
    elif msg.startswith("OK"):
        print("✅",tbp)
    elif msg.startswith("INFO"):
        print("➡️",tbp)
    elif msg.startswith("DET"):
        print("🔍",tbp)
    else:
        print(tbp)


def verify_field_existence (messages,campi,lab, keys):
    for campo in campi:
        if not (lab[campo] in keys):
            message(messages,"ERROR_MISSING_KEY",{"key":lab[campo]})

def verify_mcq_choices(messages, risp, lab):
    for i in range(len(risp[lab["statements"]])):
        if str(i+1) not in risp[lab["group_fractions"]].keys():
            risp[lab["group_fractions"]][str(i+1)] = "0"
    for key in risp[lab["group_fractions"]]:
        risp[lab["group_fractions"]][key] = risp[lab["group_fractions"]][key].replace(',','.')
    for choice in risp[lab["choices"]]:
        if int(choice[0]) != 1:
            message(messages,"ERROR_MCQ_FIRST",{"choice":choice, "choice_value":choice[0]})
        somma = sum(int(choice[i])*float(risp[lab["group_fractions"]][str(i+1)]) for i in range(1,len(choice)) if float(risp[lab["group_fractions"]][str(i+1)]) > 0)
        if somma != 100:
            message(messages,"ERROR_MCQ_SUM",{"choice":choice, "sum":somma})

        multiple_answers = lab["options"] in risp and lab["multiple"] in risp[lab["options"]] or sum(choice[int(i)-1] for i in risp[lab["group_fractions"]]
                                                                                                     if (len(choice) >= int(i) > 1 and float(risp[lab["group_fractions"]][i]) > 0) > 1)
        a_null_fraction = sum(1 for i in risp[lab["group_fractions"]]
            if (int(i) <= len(choice) and int(i) > 0 and choice[int(i)-1] > 1 and float(risp[lab["group_fractions"]][i]) == 0) > 0)
        if multiple_answers and a_null_fraction:
            message(messages,"WARNING_MCQ_ZERO",{"choice":choice})


def verify_semantics(messages,risp, istruzioni,lab):
    # first verify the existence of required fields
    verify_field_existence(messages,istruzioni["necessary_input_fields"]["all"],lab, risp.keys())
    supported_q_types = istruzioni["supported_question_types"]
    supported = False
    for q_type in supported_q_types:
        if risp[lab["question_type"]] == q_type:
            supported = True
            verify_field_existence(messages,istruzioni["necessary_input_fields"][q_type], lab,risp.keys())
    if not supported:
        q_type_list = ", ".join(supported_q_types)
        message(messages,"ERROR_UNSUPPORTED_Q_TYPE",{"qtype_list":q_type_list})
    num_aff = int(risp[lab["number_of_statements"]])
    # verify that risp[lab["statements"]] is a dictionary and that it has all keys in the range 1-num_max
    if not isinstance(risp[lab["statements"]],dict):
        message(messages,"ERROR_MUST_BE_DICT",{"key":lab["statements"]})
    num_gruppi_frasi = len(risp[lab["statements"]].keys())
    chiavi_continue = {str(i) for i in range(1, len(risp[lab["statements"]].keys())+1)}
    if risp[lab["statements"]].keys() != chiavi_continue:
           message(messages,"ERROR_MISSING_GROUP_KEYS",{"max":str(len(risp[lab["statements"]].keys())),"missing_keys":", ".join(chiavi_continue-risp[lab["statements"]].keys())} )

    for chiave, elenco in risp[lab["statements"]].items():
        for domanda in elenco:
            if isinstance(domanda, dict):
                # verify that the rich_statements have both requires fields
                if not (lab["statement"] in domanda.keys()) or not (lab["correct"] in domanda.keys()):
                    message(messages,"ERROR_MISSING_STATEMENT_KEYS",{"group":chiave,"statement_key":lab["statement"],"correct_key":lab["correct"]})

                # verify that each 'correct' field point to a specified 'answer'
                if risp[lab["question_type"]] != "mcq" and domanda[lab["correct"]] not in risp[lab["answers"]].keys():
                    message(messages,"ERROR_UNMATCHED_CORRECT_ANS",{"statement":domanda[lab["statement"]],"correct":domanda[lab["correct"]],"answers_key":lab["answers"]})
                #verify that each dd question has a hole to be filled
                if risp[lab["question_type"]] == "dd" and not risp[lab["answer_placeholder"]] in domanda[lab["statement"]]:
                    message(messages,"ERROR_MISSING_HOLE",{"statement":domanda[lab["statement"]],"place_holder":risp[lab["answer_placeholder"]]})


    # verify that choices (if existing) make sense
    if lab["choices"] in risp.keys() and (len(risp[lab["choices"]]))>0:
        for lista in risp[lab["choices"]]:
            if len(lista) > num_gruppi_frasi:
                message(messages,"ERROR_TOO_LONG_CHOICE",{"choice":str(lista),"choices_key":lab["choices"],"groups_number": str(num_gruppi_frasi)})
            elif len(lista) < num_gruppi_frasi:
                message(messages,"WARNING_TOO_SHORT_CHOICE",{"choice":str(lista),"choices_key":lab["choices"],"groups_number": str(num_gruppi_frasi)})
            somma = sum(lista)
            if somma != num_aff:
                message(messages,"ERROR_CHOICE_SUM",{"choice":str(lista),"number_of_statements_key":lab["number_of_statements"],"number_of_statements": str(num_aff),"sum":str(somma)})
            for choice in risp[lab["choices"]]:
                for i in range(len(choice)):
                    if choice[i] > len(risp[lab["statements"]][str(i+1)]):
                        message(messages,"ERROR_CHOICE_INSUFF_GROUP",{"choice":choice, "group":str(i+1),"choice_value":choice[i]})
        # verifies that that the first statement (which serves as question) is always chosen exactly once (choice = 1) and that the answer fractions sum to 100
        if risp[lab["question_type"]] == "mcq":
            verify_mcq_choices(messages,risp,lab)

    if risp[lab["question_type"]] == "cloze" and not risp[lab["cloze_type"]] in istruzioni["cloze_types"]["one_answer"]:
                message(messages,"ERROR_UNSUPPORTED_CLOZE",{"cloze_type":risp[lab["cloze_type"]],"cloze_type_list": ", ".join(istruzioni["cloze_types"]["one_answer"])})
                # error_message('non so gestire il tipo_cloze specificato')
    # for dd questions check that for each possible answer it is specificed whether it must be infinite
    if risp[lab["question_type"]] == "dd":
        if not lab["if_infinite"] in risp.keys() or (lab["if_infinite"] in risp.keys()) and (risp[lab["if_infinite"]].keys() != risp[lab["answers"]].keys()):
            message(messages,"WARNING_UNSPECIFIED_IFINFINITE",{})

    if lab["options"] in risp.keys():
        meaningful_options = [lab[opt] for opt in istruzioni["meaningful_options"][risp[lab["question_type"]]]]
        for option in risp[lab["options"]]:
            if not option in meaningful_options:
                message(messages,"WARNING_NON_MEANINGFUL_OPTION",{"option":option})

def controlla_json_friendly(messages,percorso_file):
    try:
        with open(percorso_file, 'r', encoding='utf-8') as f:
            contenuto = f.read()
        dati = json.loads(contenuto)
        message(messages,"OK_JSON", {"path":percorso_file})
        return dati

    except FileNotFoundError:
        message(messages,"ERROR_NOTFOUND",{"path":percorso_file})
        sys.exit(1)

    except json.JSONDecodeError as e:


        # Se l'errore è "Expecting ',' delimiter" ma siamo a fine riga/fine file,
        # significa quasi sempre che manca un '}' o un ']' di chiusura.
        message(messages, "MSG_ERROR_JSON", {"json_error_message": e.msg})

        if "Expecting ',' delimiter" in e.msg:
            message(messages, "WARNING_JSON_MISSING_DELIMITER",{})
        message(messages,"MSG_JSON_LINECOL_INFO",{"line_number":e.lineno, "col_number":e.colno})
        print("-" * 50)

        righe = contenuto.splitlines()
        riga_errore_idx = e.lineno - 1

        message(messages,"DET_JSON_CODE_PREVIEW",{})

        if riga_errore_idx > 0:
            print(f"   {e.lineno - 1:4d} | {righe[riga_errore_idx - 1]}")

        if riga_errore_idx < len(righe):
            riga_corrente = righe[riga_errore_idx]

            print(f"👉 {e.lineno:4d} | {riga_corrente}")
            spazi = " " * max(0, e.colno - 1)+"         "
            message(messages, "MSG_spaces", {"spaces": spazi})

        if riga_errore_idx < len(righe) - 1:
            print(f"   {e.lineno + 1:4d} | {righe[riga_errore_idx + 1]}")

        print("-" * 50)
        sys.exit(1)