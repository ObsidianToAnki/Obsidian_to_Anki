import { Notice, Plugin, addIcon } from 'obsidian'
import * as AnkiConnect from './src/anki'
import { PluginSettings, ParsedSettings } from './src/interfaces/settings-interface'
import { SettingsTab } from './src/settings'
import { ANKI_ICON } from './src/constants'
import { settingToData } from './src/setting-to-data'
import { FileManager } from './src/files-manager'

export default class MyPlugin extends Plugin {

	settings: PluginSettings
	note_types: Array<string>
	added_media: string[]
	file_hashes: Record<string, string>

	async own_saveData(data_key: string, data: any): Promise<void> {
		let current_data = await this.loadData()
		current_data[data_key] = data
		this.saveData(current_data)
	}

	async getDefaultSettings(): Promise<PluginSettings> {
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

	async saveDefault(): Promise<void> {
		const default_sets = await this.getDefaultSettings()
		this.saveData(
			{
				settings: default_sets,
				"Added Media": [],
				"File Hashes": {}
			}
		)
	}

	async loadSettings(): Promise<PluginSettings> {
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

	async loadAddedMedia(): Promise<string[]> {
		let current_data = await this.loadData()
		if (current_data == null) {
			await this.saveDefault()
			return []
		} else {
			return current_data["Added Media"]
		}
	}

	async loadFileHashes(): Promise<Record<string, string>> {
		let current_data = await this.loadData()
		if (current_data == null) {
			await this.saveDefault()
			return {}
		} else {
			return current_data["File Hashes"]
		}
	}

	async saveAllData(): Promise<void> {
		this.saveData(
				{
					settings: this.settings,
					"Added Media": this.added_media,
					"File Hashes": this.file_hashes
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
		this.added_media = await this.loadAddedMedia()
		this.file_hashes = await this.loadFileHashes()

		this.addSettingTab(new SettingsTab(this.app, this));

		this.addRibbonIcon('anki', 'Obsidian_to_Anki - Scan Vault', async () => {
			new Notice('Scanning vault, check console for details...');
			const data: ParsedSettings = await settingToData(this.settings, this.app)
			const manager = new FileManager(this.app, data, this.app.vault.getMarkdownFiles(), this.file_hashes, this.added_media)
			await manager.initialiseFiles()
			await manager.requests_1()
			this.added_media = Array.from(manager.added_media_set)
			const hashes = manager.getHashes()
			for (let key in hashes) {
				this.file_hashes[key] = hashes[key]
			}
			this.saveAllData()
		})
	}

	async onunload() {
		console.log("Saving settings for Obsidian_to_Anki...")
		this.saveAllData()
		console.log('unloading Obsidian_to_Anki...');
	}
}
