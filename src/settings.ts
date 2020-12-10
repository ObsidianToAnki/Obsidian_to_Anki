import { PluginSettingTab, Setting } from 'obsidian'
import * as AnkiConnect from './anki'

export class SettingsTab extends PluginSettingTab {

	setup_table() {
		let {containerEl} = this;
		const plugin = (this as any).plugin
		containerEl.createEl('h3', {text: 'Note type settings'})
		let note_type_table = containerEl.createEl('table', {cls: "anki-settings-table"})
		let head = note_type_table.createTHead()
		let header_row = head.insertRow()
		for (let header of ["Note Type", "Custom Regexp"]) {
			let th = document.createElement("th")
			th.appendChild(document.createTextNode(header))
			header_row.appendChild(th)
		}
		let main_body = note_type_table.createTBody()
		for (let note_type of plugin.note_types) {
			let row = main_body.insertRow()
			row.insertCell()
			row.insertCell()
			let row_cells = row.children
			row_cells[0].innerHTML = note_type
			let regexp_section = plugin.settings["CUSTOM_REGEXPS"]
			let custom_regexp = new Setting(row_cells[1] as HTMLElement)
				.addText(
						text => text.setValue(
						regexp_section.hasOwnProperty(note_type) ? regexp_section[note_type] : ""
						)
						.onChange((value) => {
							plugin.settings["CUSTOM_REGEXPS"][note_type] = value
							plugin.saveAllData()
						})
				)
			custom_regexp.settingEl = row_cells[1] as HTMLElement
			custom_regexp.infoEl.remove()
			custom_regexp.controlEl.className += " anki-center"
		}
	}

	setup_syntax() {
		let {containerEl} = this;
		const plugin = (this as any).plugin
		let syntax_settings = containerEl.createEl('h3', {text: 'Syntax Settings'})
		for (let key of Object.keys(plugin.settings["Syntax"])) {
			new Setting(syntax_settings)
				.setName(key)
				.addText(
						text => text.setValue(plugin.settings["Syntax"][key])
						.onChange((value) => {
							plugin.settings["Syntax"][key] = value
							plugin.saveAllData()
						})
				)
		}
	}

	setup_defaults() {
		let {containerEl} = this;
		const plugin = (this as any).plugin
		let defaults_settings = containerEl.createEl('h3', {text: 'Defaults'})
		for (let key of Object.keys(plugin.settings["Defaults"])) {
			if (typeof plugin.settings["Defaults"][key] === "string") {
				new Setting(defaults_settings)
					.setName(key)
					.addText(
						text => text.setValue(plugin.settings["Defaults"][key])
						.onChange((value) => {
							plugin.settings["Defaults"][key] = value
							plugin.saveAllData()
						})
				)
			} else {
				new Setting(defaults_settings)
					.setName(key)
					.addToggle(
						toggle => toggle.setValue(plugin.settings["Defaults"][key])
						.onChange((value) => {
							plugin.settings["Defaults"][key] = value
							plugin.saveAllData()
						})
					)
			}
		}
	}

	setup_buttons() {
		let {containerEl} = this
		const plugin = (this as any).plugin
		let action_buttons = containerEl.createEl('h3', {text: 'Actions'})
		new Setting(action_buttons)
			.setName("Regenerate Table")
			.setDesc("Connect to Anki to regenerate the table with new note types, or get rid of deleted note types.")
			.addButton(
				button => {
					button.setButtonText("Regenerate")
					.onClick(async () => {
						plugin.note_types = await AnkiConnect.invoke('modelNames')
						plugin.regenerateSettingsRegexps()
						await plugin.saveAllData()
						this.setup_display()
					})
				}
			)
		new Setting(action_buttons)
			.setName("Clear Media Cache")
			.setDesc(`Clear the cached list of media filenames that have been added to Anki.

			The script will skip over adding a media file if it's added a file with the same name before, so clear this if e.g. you've updated the media file with the same name.`)
			.addButton(
				button => {
					button.setButtonText("Clear")
					.onClick(async () => {
						plugin.added_media = []
						await plugin.saveAllData()
					})
				}
			)
		new Setting(action_buttons)
			.setName("Clear File Hash Cache")
			.setDesc(`Clear the cached dictionary of file hashes that the script has scanned before.

			The script will skip over a file if the file path and the hash is unaltered.`)
			.addButton(
				button => {
					button.setButtonText("Clear")
					.onClick(async () => {
						plugin.file_hashes = {}
						await plugin.saveAllData()
					})
				}
			)
	}

	setup_display() {
		let {containerEl} = this

		containerEl.empty()
		containerEl.createEl('h2', {text: 'Obsidian_to_Anki settings'})
		this.setup_table()
		this.setup_syntax()
		this.setup_defaults()
		this.setup_buttons()
	}

	async display() {
		this.setup_display()
	}
}
