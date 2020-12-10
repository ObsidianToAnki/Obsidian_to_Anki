import { App, Modal, Notice, Plugin, PluginSettingTab, Setting, addIcon, getLinkpath, TFile } from 'obsidian'
import * as AnkiConnect from './src/anki'
import { PluginSettings, ExternalAppData } from './src/interfaces/settings-interface'
import { SettingsTab } from './src/settings'
import { ANKI_ICON } from './src/constants'
import { settingToData } from './src/setting-to-data'
import { FileManager } from './src/files-manager'

/* Declaring initial variables*/

let ID_PREFIX: string = "ID: ";

let TAG_PREFIX: string = "Tags: ";
let TAG_SEP: string = " ";

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
				"Delete Note Line": "DELETE",
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
		addIcon('anki', ANKI_ICON)

		this.settings = await this.loadSettings()
		this.note_types = Object.keys(this.settings["CUSTOM_REGEXPS"])

		this.addRibbonIcon('anki', 'Obsidian_to_Anki', () => {
			new Notice('Cool icon!');
		})

		/*
		this.addStatusBarItem().setText('Status Bar Text');
		*/

		this.addCommand({
			id: 'open-sample-modal',
			name: 'Open Sample Modal',
			/*
			callback: () => {
			 	console.log('Simple Callback');
			 },
			*/
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

		const data: ExternalAppData = await settingToData(this.settings, this.app)

		const testFile = this.app.vault.getAbstractFileByPath("hap.md") as TFile
		const manager = new FileManager(this.app, data, [testFile], {})

		await manager.initialiseFiles()
		await manager.requests_1()

		/*
		this.registerEvent(this.app.on('codemirror', (cm: CodeMirror.Editor) => {
			console.log('codemirror', cm);
		}));

		this.registerDomEvent(document, 'click', (evt: MouseEvent) => {
			console.log('click', evt);
		});

		this.registerInterval(window.setInterval(() => console.log('setInterval'), 5 * 60 * 1000));
		*/
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
