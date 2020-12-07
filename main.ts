import { App, Modal, Notice, Plugin, PluginSettingTab, Setting } from 'obsidian';

/* Declaring initial variables*/

let MEDIA: Record<string, string> = {};

let ID_PREFIX: string = "ID: ";
let TAG_PREFIX: string = "Tags: ";
let TAG_SEP: string = " ";

interface NOTE_DICT_OPTIONS {
	allowDuplicate: boolean,
	duplicateScope: string,
};

interface NOTE_DICT {
	deckName: string,
	modelName: string,
	fields: Record<string, string>,
	options: NOTE_DICT_OPTIONS,
	tags: Array<string>,
	audio: Array<any>
};

let NOTE_DICT_TEMPLATE: NOTE_DICT = {
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



export default class MyPlugin extends Plugin {
	onload() {
		console.log('loading plugin');

		this.addRibbonIcon('dice', 'Sample Plugin', () => {
			new Notice('This is a notice!');
		});

		this.saveData(10)

		console.log(this.loadData())

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
	display(): void {
		let {containerEl} = this;

		containerEl.empty();

		containerEl.createEl('h2', {text: 'Settings for my awesome plugin.'});

		new Setting(containerEl)
			.setName('Setting #1')
			.setDesc('It\'s a secret')
			.addText(text => text.setPlaceholder('Enter your secret')
				.setValue('')
				.onChange((value) => {
					console.log('Secret: ' + value);
				}));

	}
}
