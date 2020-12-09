import { App, Modal, Notice, Plugin, PluginSettingTab, Setting } from 'obsidian'
import { NOTE } from './src/interfaces/note-interface'
import { basename } from 'path'
import * as AnkiConnect from './src/anki'
import { PluginSettings } from './src/interfaces/settings-interface'
import { SettingsTab } from './src/settings'
import { Note, InlineNote } from './src/note'

/* Declaring initial variables*/

let ID_PREFIX: string = "ID: ";

let TAG_PREFIX: string = "Tags: ";
let TAG_SEP: string = " ";

const ANKI_CLOZE_REGEXP: RegExp = /{{c\d+::[\s\S]+?}}/g

function has_clozes(text: string): boolean {
	/*Checks whether text actually has cloze deletions.*/
	return ANKI_CLOZE_REGEXP.test(text)
}

function note_has_clozes(note: NOTE): boolean {
	/*Checks whether a note has cloze deletions in any of its fields.*/
	return Array(note.fields.values).some(has_clozes)
}

function string_insert(text: string, position_inserts: Array<[number, string]>): string {
	/*Insert strings in position_inserts into text, at indices.

    position_inserts will look like:
    [(0, "hi"), (3, "hello"), (5, "beep")]*/
	let offset = 0
	let sorted_inserts: Array<[number, string]> = position_inserts.sort((a, b):number => a[0] - b[0])
	for (let insertion of sorted_inserts) {
		let position = insertion[0]
		let insert_str = insertion[1]
		text = text.slice(0, position + offset) + insert_str + text.slice(position + offset)
		offset += insert_str.length
	}
	return text
}

function spans(pattern: RegExp, text: string): Array<[number, number]> {
	/*Return a list of span-tuples for matches of pattern in text.*/
	let output: Array<[number, number]> = []
	let matches = text.matchAll(pattern)
	for (let match of matches) {
		output.push(
			[match.index, match.index + match.length]
		)
	}
	return output
}

function contained_in(span: [number, number], spans: Array<[number, number]>): boolean {
	/*Return whether span is contained in spans (+- 1 leeway)*/
	return spans.some(
		(element) => span[0] >= element[0] - 1 && span[1] <= element[1] + 1
	)
}

function* findignore(pattern: RegExp, text: string, ignore_spans: Array<[number, number]>): IterableIterator<RegExpMatchArray> {
	let matches = text.matchAll(pattern)
	for (let match of matches) {
		if (!(contained_in([match.index, match.index + match.length], ignore_spans))) {
			yield match
		}
	}
}

const test = `Basic
This is a test.
Back: Test successful!
Front: More content
and even more!!!
$x = 5$ stuff too.
# and a markdown heading...

Tags: Help halp holp
<!--ID: 124090124940-->`

const test2 = "[Basic] This is a test. Back: Test successful! Front: More content Tags: Help halp <!--ID: 124901421-->"

const fields_dict = {
	Basic: ['Front', 'Back']
}

export default class MyPlugin extends Plugin {

	settings: PluginSettings
	note_types: Array<string>

	async own_saveData(data_key: string, data: any) {
		let current_data = await this.loadData()
		current_data[data_key] = data
		this.saveData(current_data)
	}

	async getDefaultSettings() {
		let settings: PluginSettings = {
			CUSTOM_REGEXPS: {},
			Syntax: {
				"Begin Note": "START",
				"End Note": "END",
				"Begin Inline Note": "STARTI",
				"End Inline Note": "ENDI",
				"Target Deck Line": "TARGET DECK",
				"File Tags Line": "FILE TAGS",
				"Delete Regex Note Line": "DELETE",
				"Frozen Fields Line": "FROZEN"
			},
			Defaults: {
				"Add File Link": false,
				"Tag": "Obsidian_to_Anki",
				"Deck": "Default",
				"CurlyCloze": false,
				"Regex": false,
				"ID Comments": true,
			}
		}
		/*Making settings from scratch, so need note types*/
		for (let note_type of await AnkiConnect.invoke('modelNames') as Array<string>) {
			settings["CUSTOM_REGEXPS"][note_type] = ""
		}
		return settings
	}

	async loadSettings() {
		let current_data = await this.loadData()
		if (current_data == null) {
			const default_sets = await this.getDefaultSettings()
			this.saveData(
				{
					settings: default_sets,
					"Added Media": [],
					"File Hashes": {}
				}
			)
			return default_sets
		} else {
			return current_data.settings
		}
	}

	async saveSettings() {
		this.saveData(
				{
					settings: this.settings,
					"Added Media": [],
					"File Hashes": {}
				}
		)
	}

	regenerateSettingsRegexps() {
		let regexp_section = this.settings["CUSTOM_REGEXPS"]
		// For new note types
		for (let note_type of this.note_types) {
			this.settings["CUSTOM_REGEXPS"][note_type] = regexp_section.hasOwnProperty(note_type) ? regexp_section[note_type] : ""
		}
		// Removing old note types
		for (let note_type of Object.keys(this.settings["CUSTOM_REGEXPS"])) {
			if (!this.note_types.includes(note_type)) {
				delete this.settings["CUSTOM_REGEXPS"][note_type]
			}
		}
	}

	async onload() {
		console.log('loading Obsidian_to_Anki...');

		this.settings = await this.loadSettings()
		this.note_types = Object.keys(this.settings["CUSTOM_REGEXPS"])

		this.addRibbonIcon('dice', 'Sample Plugin', () => {
			new Notice('This is a notice!');
		});

		this.addStatusBarItem().setText('Status Bar Text');

		this.addCommand({
			id: 'open-sample-modal',
			name: 'Open Sample Modal',
			// callback: () => {
			// 	console.log('Simple Callback');
			// },
			checkCallback: (checking: boolean) => {
				let leaf = this.app.workspace.activeLeaf;
				if (leaf) {
					if (!checking) {
						new SampleModal(this.app).open();
					}
					return true;
				}
				return false;
			}
		});

		this.addSettingTab(new SettingsTab(this.app, this));

		this.registerEvent(this.app.on('codemirror', (cm: CodeMirror.Editor) => {
			console.log('codemirror', cm);
		}));

		this.registerDomEvent(document, 'click', (evt: MouseEvent) => {
			console.log('click', evt);
		});

		this.registerInterval(window.setInterval(() => console.log('setInterval'), 5 * 60 * 1000));
	}

	async onunload() {
		console.log("Saving settings for Obsidian_to_Anki...")
		this.saveSettings()
		console.log('unloading Obsidian_to_Anki...');
	}
}

class SampleModal extends Modal {
	constructor(app: App) {
		super(app);
	}

	onOpen() {
		let {contentEl} = this;
		contentEl.setText('Woah!');
	}

	onClose() {
		let {contentEl} = this;
		contentEl.empty();
	}
}
