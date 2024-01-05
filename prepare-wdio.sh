#!/bin/bash

mkdir -p tests/test_config
mkdir -p tests/test_vault
mkdir -p tests/specs_gen
mkdir -p tests/test_outputs

# Copy Built plugin
rm -rf tests/defaults/test_vault/.obsidian/plugins/obsidian-to-anki-plugin 
mkdir -p tests/defaults/test_vault/.obsidian/plugins/obsidian-to-anki-plugin 
cp manifest.json styles.css main.js tests/defaults/test_vault/.obsidian/plugins/obsidian-to-anki-plugin/

# Setup docker volumes
rm -rf tests/test_vault 
rm -rf tests/test_config 

cp -Rf tests/defaults/test_vault tests/ 
cp -Rf tests/defaults/test_config tests/
