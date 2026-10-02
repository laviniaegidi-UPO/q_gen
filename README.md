The program `q_gen` allows generating question collections in Moodle XML format
starting from input files. The input files list the alternatives to be used and other
information for the preparation of the questions (question type, category, title,
etc.). The produced files can be imported into Moodle.

The program is capable of producing questions of the following types:

* multiple choice
* drag\&drop
* single-choice cloze
* open cloze

The program's interface can be easily translated to any language by customizing the configuration file. A configuration file for usage in English (`config_en.json`) and one for usage in Italian (`config_it.json`) are provided. The program uses by default file `config.json` for its configuration, that in this realease is a copy of the Italian configuration file. Just rename `config_en.json` to `config.json` to switch to English or use the `-c` option (see below).


The program is distributed without any warranty, in the hope that it may be useful to others. It is recommended to verify that the produced questions are correct before using them, as there may be errors in the program or the meaning of some options may not be clear.
It is not complete, it supports question types and cases that have been useful to me.
It is distributed with a few examples that can help understand the required format for the input files.

A detailed manual is included, both in Italian and in English. This is just a brief summary of the commands.

usage: 
`q_gen [-h] [-i INPUT_FILE] [-s SOURCE_DIRECTORY] [-o OUT_DIR]
             [-j JOIN_DIR] [-c CONFIG_FILE] [-v JSON_FILE_TO_BE_VERIFIED]`

generates collections of questions in XML Moodle format from input JSON files

options:

    -h, --help            show this help message and exit

    -i, --input_file INPUT_FILE  
                        input file
    -s, --source_directory SOURCE_DIRECTORY
                        process all files in the specified source directory
    -o, --out_dir OUT_DIR
                        output directory
    -j, --join_dir JOIN_DIR
                        join all XML files from the specified join_directory
                        (if there is already a join file, it is disregarded)
    -c, --config_file CONFIG_FILE
                        use specified config_file as configuration file
                        (default is config.json); the config_file must be in
                        JSON format
    -v, --verify_json_file JSON_FILE_TO_BE_VERIFIED
                        verify that the JSON input file is syntactically
                        correct (useful after preparing new configuration
                        files)

