import { App, Modal, Notice, Plugin, PluginSettingTab, Setting } from 'obsidian';
import {Converter} from 'showdown'

let converter = new Converter()

/* Declaring initial variables*/

let MEDIA: Record<string, string> = {};

let ID_PREFIX: string = "ID: ";
let TAG_PREFIX: string = "Tags: ";
let TAG_SEP: string = " ";

interface NOTE_OPTIONS {
	allowDuplicate: boolean,
	duplicateScope: string,
};

interface NOTE {
	deckName: string,
	modelName: string,
	fields: Record<string, string>,
	options: NOTE_OPTIONS,
	tags: Array<string>,
	audio: Array<any>
};

let NOTE_DICT_TEMPLATE: NOTE = {
	deckName: "",
	modelName: "",
	fields: {},
	options: {
		allowDuplicate: false,
		duplicateScope: "deck",
	},
	tags: ["Obsidian_to_Anki"],
	audio: [],
};

let CONFIG_DATA = {}

const ANKI_PORT: number = 8765

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

interface AnkiConnectRequest {
	action: string,
	params: any,
	version: number
}

class AnkiConnect {
	static request(action: string, params={}) {
		return {action, version:6, params}
	}

	static invoke(action: string, params={}) {
	    return new Promise((resolve, reject) => {
	        const xhr = new XMLHttpRequest();
	        xhr.addEventListener('error', () => reject('failed to issue request'));
	        xhr.addEventListener('load', () => {
	            try {
	                const response = JSON.parse(xhr.responseText);
	                if (Object.getOwnPropertyNames(response).length != 2) {
	                    throw 'response has an unexpected number of fields';
	                }
	                if (!response.hasOwnProperty('error')) {
	                    throw 'response is missing required error field';
	                }
	                if (!response.hasOwnProperty('result')) {
	                    throw 'response is missing required result field';
	                }
	                if (response.error) {
	                    throw response.error;
	                }
	                resolve(response.result);
	            } catch (e) {
	                reject(e);
	            }
	        });

	        xhr.open('POST', 'http://127.0.0.1:8765');
	        xhr.send(JSON.stringify({action, version: 6, params}));
	    });
	}
}

class FormatConverter {
	static OBS_INLINE_MATH_REGEXP = /(?<!\$)\$((?=[\S])(?=[^$])[\s\S]*?\S)\$/g
	static OBS_DISPLAY_MATH_REGEXP = /\$\$([\s\S]*?)\$\$/g
	static OBS_CODE_REGEXP = /(?<!`)`(?=[^`])[\s\S]*?`/g
	static OBS_DISPLAY_CODE_REGEXP = /```[\s\S]*?```/g

	static ANKI_MATH_REGEXP = /(\\\[[\s\S]*?\\\])|(\\\([\s\S]*?\\\))/g

	static MATH_REPLACE = "OBSTOANKIMATH"

	static IMAGE_REGEXP = /<img alt=".*?" src="(.*?)"/g
	static SOUND_REGEXP = /\[sound:(.+)\]/g
	static CLOZE_REGEXP = /(?:(?<!{){(?:c?(\d+)[:|])?(?!{))((?:[^\n][\n]?)+?)(?:(?<!})}(?!}))/g
	static URL_REGEXP = /https?:///g

	static PARA_OPEN = "<p>"
	static PARA_CLOSE = "</p>"

	static CLOZE_UNSET_NUM = 1

	static format_note_with_url(note: NOTE, url: string): void {
		for (let field in note.fields) {
			note.fields[field] += '<br><a href="' + url + '" class="obsidian-link">Obsidian</a>'
		}
	}

	static format_note_with_frozen_fields(note: NOTE, frozen_fields_dict): void {
		for (let field in note.fields) {
			note.fields[field] += frozen_fields_dict[note.modelName][field]
		}
	}

	static obsidian_to_anki_math(note_text: string): string {
		return note_text.replace(
				FormatConverter.OBS_DISPLAY_MATH_REGEXP, "\\[$1\\]"
		).replace(
			FormatConverter.OBS_INLINE_MATH_REGEXP,
			"\\($1\\)"
		)
	}

	static cloze_repl(match: string, match_id: string, match_content: string): string {
		if (match_id == undefined) {
			let result = "{{c" + FormatConverter.CLOZE_UNSET_NUM.toString() + "::" + match_content + "}}"
			FormatConverter.CLOZE_UNSET_NUM += 1
			return result
		}
		let result = "{{c" + match_id + "::" + match_content + "}}"
		return result
	}

	static curly_to_cloze(text: string): string {
		/*Change text in curly brackets to Anki-formatted cloze.*/
		text = text.replaceAll(FormatConverter.CLOZE_REGEXP, FormatConverter.cloze_repl)
		FormatConverter.CLOZE_UNSET_NUM = 1
		return text
	}


}

let test = `# This is some markdown testing!`

let testtable = `<table style="width:100%">
  <tr>
    <th>Firstname</th>
    <th>Lastname</th>
    <th>Age</th>
  </tr>
  <tr>
    <td>Jill</td>
    <td>Smith</td>
    <td>50</td>
  </tr>
  <tr>
    <td>Eve</td>
    <td>Jackson</td>
    <td>94</td>
  </tr>
</table>`

interface PluginSettings {
	CUSTOM_REGEXPS: Record<string, string>,
	Syntax: {
		"Begin Note": string,
		"End Note": string,
		"Begin Inline Note": string,
		"End Inline Note": string,
		"Target Deck Line": string,
		"File Tags Line": string,
		"Delete Regex Note Line": string,
		"Frozen Fields Line": string
	},
	Obsidian: {
		"Add File Link": boolean,
	},
	Defaults: {
		"Tag": string,
		"Deck": string,
		"CurlyCloze": boolean,
		"Regex": boolean,
		"ID Comments": boolean,
	}
}

export default class MyPlugin extends Plugin {

	settings: PluginSettings

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
			Obsidian: {
				"Add File Link": false,
			},
			Defaults: {
				"Tag": "Obsidian_to_Anki",
				"Deck": "Default",
				"CurlyCloze": false,
				"Regex": false,
				"ID Comments": true,
			}
		}
		for (let note_type of await AnkiConnect.invoke('modelNames') as Array<string>) {
			settings["CUSTOM_REGEXPS"][note_type] = ""
		}
		return settings
	}

	async loadSettings() {
		let current_data = await this.loadData()
		if (current_data == null) {
			const default_sets = await this.getDefaultSettings()
			await this.saveData(
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

	async onload() {
		console.log('loading plugin');

		this.settings = await this.loadSettings()
		console.log(this.settings)

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

		this.addSettingTab(new SampleSettingTab(this.app, this));

		this.registerEvent(this.app.on('codemirror', (cm: CodeMirror.Editor) => {
			console.log('codemirror', cm);
		}));

		this.registerDomEvent(document, 'click', (evt: MouseEvent) => {
			console.log('click', evt);
		});

		this.registerInterval(window.setInterval(() => console.log('setInterval'), 5 * 60 * 1000));
	}

	onunload() {
		console.log('unloading plugin');
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

class SampleSettingTab extends PluginSettingTab {

	constructor(app: App, plugin) {
		super(app, plugin)
	}

	async display() {
		let {containerEl} = this;

		containerEl.empty();
		containerEl.createEl('h2', {text: 'Obsidian_to_Anki settings'});

		containerEl.createEl('h3', {text: 'Note type settings'})
		let note_type_table = containerEl.createEl('table', {cls: "anki-settings-table"});
		console.log(getComputedStyle(note_type_table).getPropertyValue('--background-modifier-border'))
		let head = note_type_table.createTHead()
		let header_row = head.insertRow()
		for (let header of ["Note Type", "Custom Regexp"]) {
			let th = document.createElement("th")
			th.appendChild(document.createTextNode(header))
			header_row.appendChild(th)
		}
		let main_body = note_type_table.createTBody()
		for (let note_type of await AnkiConnect.invoke('modelNames') as Array<string>) {
			let row = main_body.insertRow()
			row.insertCell()
			row.insertCell()
			let row_cells = row.children
			row_cells[0].innerHTML = note_type

			let custom_regexp = new Setting(row_cells[1] as HTMLElement)
			custom_regexp.settingEl = row_cells[1] as HTMLElement
			custom_regexp.infoEl.remove()
			custom_regexp.addText(text => text.setValue(""))
			custom_regexp.controlEl.className += " anki-center"
		}

		let syntax_settings = containerEl.createEl('h3', {text: 'Syntax Settings'})
		let NOTE_PREFIX = new Setting(syntax_settings).setName("Begin Note").addText(text => text.setValue("START"))


		/*
		new Setting(containerEl)
			.setName('Setting #1')
			.setDesc('It\'s a secret')
			.addText(text => text.setPlaceholder('Enter your secret')
				.setValue('')
				.onChange((value) => {
					console.log('Secret: ' + value);
				}));
		*/

	}
}
