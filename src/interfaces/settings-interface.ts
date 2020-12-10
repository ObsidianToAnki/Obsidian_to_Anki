import { FIELDS_DICT, FROZEN_FIELDS_DICT } from './field-interface'
import { AnkiConnectNote } from './note-interface'

export interface PluginSettings {
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
	Defaults: {
		"Add File Link": boolean,
		"Tag": string,
		"Deck": string,
		"CurlyCloze": boolean,
		"Regex": boolean,
		"ID Comments": boolean,
	}
}

export interface ExternalAppData {
    vault_name: string
    fields_dict: FIELDS_DICT

    FROZEN_REGEXP: RegExp
    DECK_REGEXP: RegExp
    TAG_REGEXP: RegExp
    NOTE_REGEXP: RegExp
    INLINE_REGEXP: RegExp
    EMPTY_REGEXP: RegExp

    curly_cloze: boolean
    template: AnkiConnectNote
    EXISTING_IDS: number[]
    add_file_link: boolean
    comment: boolean
	regex: boolean
	custom_regexps: Record<string, string>
}
