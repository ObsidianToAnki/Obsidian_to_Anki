import { PluginSettingTab, Setting, Notice } from 'obsidian'
import * as AnkiConnect from './anki'

const defaultDescs = {
	"Tag": "The tag that the plugin automatically adds to any generated cards.",
	"Deck": "The deck the plugin adds cards to if TARGET DECK is not specified in the file.",
	"Scheduling Interval": "The time, in minutes, between automatic scans of the vault. Set this to 0 to disable automatic scanning.",
	"Add File Link": "Append a link to the file that generated the flashcard on the field specified in the table.",
	"Add Context": "Append 'context' for the card, in the form of path > heading > heading etc, to the field specified in the table.",
	"CurlyCloze": "Convert {cloze deletions} -> {{c1::cloze deletions}} on note types that have a 'Cloze' in their name.",
	"CurlyCloze - Highlights to Clozes": "Convert ==highlights== -> {highlights} to be processed by CurlyCloze.",
	"ID Comments": "Wrap note IDs in a HTML comment."
}

export class SettingsTab extends PluginSettingTab {

	setup_custom_regexp(note_type: string, row_cells: HTMLCollection) {
		const plugin = (this as any).plugin
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

	setup_link_field(note_type: string, row_cells: HTMLCollection) {
		const plugin = (this as any).plugin
		let link_fields_section = plugin.settings.FILE_LINK_FIELDS
		let link_field = new Setting(row_cells[2] as HTMLElement)
			.addDropdown(
				async dropdown => {
					if (!(plugin.fields_dict[note_type])) {
						plugin.fields_dict = await plugin.loadFieldsDict()
						if (Object.keys(plugin.fields_dict).length != plugin.note_types.length) {
							new Notice('Need to connect to Anki to generate fields dictionary...')
							try {
								plugin.fields_dict = await plugin.generateFieldsDict()
								new Notice("Fields dictionary successfully generated!")
							}
							catch(e) {
								new Notice("Couldn't connect to Anki! Check console for error message.")
								return
							}
						}
					}
					const field_names = plugin.fields_dict[note_type]
					for (let field of field_names) {
						dropdown.addOption(field, field)
					}
					dropdown.setValue(
						link_fields_section.hasOwnProperty(note_type) ? link_fields_section[note_type] : field_names[0]
					)
					dropdown.onChange((value) => {
						plugin.settings.FILE_LINK_FIELDS[note_type] = value
						plugin.saveAllData()
					})
				}
			)
		link_field.settingEl = row_cells[2] as HTMLElement
		link_field.infoEl.remove()
		link_field.controlEl.className += " anki-center"
	}

	setup_context_field(note_type: string, row_cells: HTMLCollection) {
		const plugin = (this as any).plugin
		let context_fields_section: Record<string, string> = plugin.settings.CONTEXT_FIELDS
		let context_field = new Setting(row_cells[3] as HTMLElement)
			.addDropdown(
				async dropdown => {
					const field_names = plugin.fields_dict[note_type]
					for (let field of field_names) {
						dropdown.addOption(field, field)
					}
					dropdown.setValue(
						context_fields_section.hasOwnProperty(note_type) ? context_fields_section[note_type] : field_names[0]
					)
					dropdown.onChange((value) => {
						plugin.settings.CONTEXT_FIELDS[note_type] = value
						plugin.saveAllData()
					})
				}
			)
		context_field.settingEl = row_cells[3] as HTMLElement
		context_field.infoEl.remove()
		context_field.controlEl.className += " anki-center"
	}

	setup_table() {
		let {containerEl} = this;
		const plugin = (this as any).plugin
		containerEl.createEl('h3', {text: 'Note type settings'})
		let div = containerEl.createEl('div', {cls: "collapsible-item"})
		div.innerHTML = `
			<div class="collapsible-item-self"><div class="collapsible-item-collapse collapse-icon anki-rotated"><svg viewBox="0 0 100 100" width="8" height="8" class="right-triangle"><path fill="currentColor" stroke="currentColor" d="M94.9,20.8c-1.4-2.5-4.1-4.1-7.1-4.1H12.2c-3,0-5.7,1.6-7.1,4.1c-1.3,2.4-1.2,5.2,0.2,7.6L43.1,88c1.5,2.3,4,3.7,6.9,3.7 s5.4-1.4,6.9-3.7l37.8-59.6C96.1,26,96.2,23.2,94.9,20.8L94.9,20.8z"></path></svg></div><div class="collapsible-item-inner"></div><header >Note Type Table</header></div>
		`
		div.addEventListener('click', function () {
			this.classList.toggle("active")
			let icon = this.firstElementChild.firstElementChild as HTMLElement
			icon.classList.toggle("anki-rotated")
			let content = this.nextElementSibling as HTMLElement
			if (content.style.display === "block") {
				content.style.display = "none"
			} else {
				content.style.display = "block"
			}
		})
		let note_type_table = containerEl.createEl('table', {cls: "anki-settings-table"})
		let head = note_type_table.createTHead()
		let header_row = head.insertRow()
		for (let header of ["Note Type", "Custom Regexp", "File Link Field", "Context Field"]) {
			let th = document.createElement("th")
			th.appendChild(document.createTextNode(header))
			header_row.appendChild(th)
		}
		let main_body = note_type_table.createTBody()
		if (!(plugin.settings.hasOwnProperty("CONTEXT_FIELDS"))) {
			plugin.settings.CONTEXT_FIELDS = {}
		}
		for (let note_type of plugin.note_types) {
			let row = main_body.insertRow()

			row.insertCell()
			row.insertCell()
			row.insertCell()
			row.insertCell()

			let row_cells = row.children

			row_cells[0].innerHTML = note_type
			this.setup_custom_regexp(note_type, row_cells)
			this.setup_link_field(note_type, row_cells)
			this.setup_context_field(note_type, row_cells)
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

		// To account for new add context
		if (!(plugin.settings["Defaults"].hasOwnProperty("Add Context"))) {
			plugin.settings["Defaults"]["Add Context"] = false
		}
		// To account for new scheduling interval
		if (!(plugin.settings["Defaults"].hasOwnProperty("Scheduling Interval"))) {
			plugin.settings["Defaults"]["Scheduling Interval"] = 0
		}
		// To account for new highlights to clozes
		if (!(plugin.settings["Defaults"].hasOwnProperty("CurlyCloze - Highlights to Clozes"))) {
			plugin.settings["Defaults"]["CurlyCloze - Highlights to Clozes"] = false
		}
		for (let key of Object.keys(plugin.settings["Defaults"])) {
			// To account for removal of regex setting
			if (key === "Regex") {
				continue
			}
			if (typeof plugin.settings["Defaults"][key] === "string") {
				new Setting(defaults_settings)
					.setName(key)
					.setDesc(defaultDescs[key])
					.addText(
						text => text.setValue(plugin.settings["Defaults"][key])
						.onChange((value) => {
							plugin.settings["Defaults"][key] = value
							plugin.saveAllData()
						})
				)
			} else if (typeof plugin.settings["Defaults"][key] === "boolean") {
				new Setting(defaults_settings)
					.setName(key)
					.setDesc(defaultDescs[key])
					.addToggle(
						toggle => toggle.setValue(plugin.settings["Defaults"][key])
						.onChange((value) => {
							plugin.settings["Defaults"][key] = value
							plugin.saveAllData()
						})
					)
			} else {
				new Setting(defaults_settings)
					.setName(key)
					.setDesc(defaultDescs[key])
					.addSlider(
						slider => {
							slider.setValue(plugin.settings["Defaults"][key])
							.setLimits(0, 360, 5)
							.setDynamicTooltip()
							.onChange(async (value) => {
								plugin.settings["Defaults"][key] = value
								await plugin.saveAllData()
								if (plugin.hasOwnProperty("schedule_id")) {
									window.clearInterval(plugin.schedule_id)
								}
								if (value != 0) {
									plugin.schedule_id = window.setInterval(async () => await plugin.scanVault(), value * 1000 * 60)
									plugin.registerInterval(plugin.schedule_id)
								}

							})
					}
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
					button.setButtonText("Regenerate").setClass("mod-cta")
					.onClick(async () => {
						new Notice("Need to connect to Anki to update note types...")
						try {
							plugin.note_types = await AnkiConnect.invoke('modelNames')
							plugin.regenerateSettingsRegexps()
							plugin.fields_dict = await plugin.loadFieldsDict()
							if (Object.keys(plugin.fields_dict).length != plugin.note_types.length) {
								new Notice('Need to connect to Anki to generate fields dictionary...')
								try {
									plugin.fields_dict = await plugin.generateFieldsDict()
									new Notice("Fields dictionary successfully generated!")
								}
								catch(e) {
									new Notice("Couldn't connect to Anki! Check console for error message.")
									return
								}
							}
							await plugin.saveAllData()
							this.setup_display()
							new Notice("Note types updated!")
						} catch(e) {
							new Notice("Couldn't connect to Anki! Check console for details.")
						}
					})
				}
			)
		new Setting(action_buttons)
			.setName("Clear Media Cache")
			.setDesc(`Clear the cached list of media filenames that have been added to Anki.

			The plugin will skip over adding a media file if it's added a file with the same name before, so clear this if e.g. you've updated the media file with the same name.`)
			.addButton(
				button => {
					button.setButtonText("Clear").setClass("mod-cta")
					.onClick(async () => {
						plugin.added_media = []
						await plugin.saveAllData()
						new Notice("Media Cache cleared successfully!")
					})
				}
			)
		new Setting(action_buttons)
			.setName("Clear File Hash Cache")
			.setDesc(`Clear the cached dictionary of file hashes that the plugin has scanned before.

			The plugin will skip over a file if the file path and the hash is unaltered.`)
			.addButton(
				button => {
					button.setButtonText("Clear").setClass("mod-cta")
					.onClick(async () => {
						plugin.file_hashes = {}
						await plugin.saveAllData()
						new Notice("File Hash Cache cleared successfully!")
					})
				}
			)
	}

	setup_display() {
		let {containerEl} = this

		containerEl.empty()
		containerEl.createEl('h2', {text: 'Obsidian_to_Anki settings'})
		containerEl.createEl('a', {text: 'For more information check the wiki', href: "https://github.com/Pseudonium/Obsidian_to_Anki/wiki"})
		this.setup_table()
		this.setup_syntax()
		this.setup_defaults()
		this.setup_buttons()
	}

	async display() {
		this.setup_display()
	}
}
