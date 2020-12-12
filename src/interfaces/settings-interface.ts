import { FIELDS_DICT } from './field-interface'
import { AnkiConnectNote } from './note-interface'

export interface PluginSettings {
	CUSTOM_REGEXPS: Record<string, string>,
	FILE_LINK_FIELDS: Record<string, string>,
	CONTEXT_FIELDS: Record<string, string>
	Syntax: {
		"Begin Note": string,
		"End Note": string,
		"Begin Inline Note": string,
		"End Inline Note": string,
		"Target Deck Line": string,
		"File Tags Line": string,
		"Delete Note Line": string,
		"Frozen Fields Line": string
	},
	Defaults: {
		"Tag": string,
		"Deck": string,
		"Scheduling Interval": number
		"Add File Link": boolean,
		"Add Context": boolean,
		"CurlyCloze": boolean,
		"Regex": boolean,
		"ID Comments": boolean,
	}
}

export interface FileData {
	//All the data that a file would need.
	fields_dict: FIELDS_DICT
	custom_regexps: Record<string, string>
	file_link_fields: Record<string, string>
	context_fields: Record<string, string>
	template: AnkiConnectNote
	EXISTING_IDS: number[]
	vault_name: string

	FROZEN_REGEXP: RegExp
	DECK_REGEXP: RegExp
	TAG_REGEXP: RegExp
	NOTE_REGEXP: RegExp
	INLINE_REGEXP: RegExp
	EMPTY_REGEXP: RegExp

	curly_cloze: boolean
	comment: boolean
	add_context: boolean
}

export interface ParsedSettings extends FileData {
    add_file_link: boolean
	regex: boolean
}
