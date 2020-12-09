/*Manages parsing notes into a dictionary formatted for AnkiConnect.

Input must be the note text.
Does NOT deal with finding the note in the file.*/

import { FormatConverter } from './format'
import { NOTE, NOTE_AND_ID } from './interfaces/note-interface'

const TAG_PREFIX:string = "Tags: "
const TAG_SEP:string = " "

const NOTE_DICT_TEMPLATE: NOTE = {
	deckName: "",
	modelName: "",
	fields: {},
	options: {
		allowDuplicate: false,
		duplicateScope: "deck",
	},
	tags: ["Obsidian_to_Anki"],
	audio: [],
}

const ANKI_CLOZE_REGEXP: RegExp = /{{c\d+::[\s\S]+?}}/g

function has_clozes(text: string): boolean {
	/*Checks whether text actually has cloze deletions.*/
	return ANKI_CLOZE_REGEXP.test(text)
}

function note_has_clozes(note: NOTE): boolean {
	/*Checks whether a note has cloze deletions in any of its fields.*/
	return Array(note.fields.values).some(has_clozes)
}

abstract class AbstractNote {
    text: string
    split_text: string[]
    current_field_num: number
    delete: boolean
    identifier: number | null
    tags: string[]
    note_type: string
    field_names: string[]
    current_field: string
    ID_REGEXP: RegExp = /(?:<!--)?ID: (\d+)/
    formatter: FormatConverter
    curly_cloze: boolean

    constructor(note_text: string, FIELDS_DICT: Record<string, string[]>, curly_cloze: boolean = false) {
        this.text = note_text.trim()
        this.current_field_num = 0
        this.delete = false
        this.split_text = this.getSplitText()
        this.identifier = this.getIdentifier()
        this.tags = this.getTags()
        this.note_type = this.getNoteType()
        this.field_names = FIELDS_DICT[this.note_type]
        this.current_field = this.field_names[0]
        this.formatter = new FormatConverter()
        this.curly_cloze = curly_cloze
    }

    abstract getSplitText(): string[]

    abstract getIdentifier(): number | null

    abstract getTags(): string[]

    abstract getNoteType(): string

    abstract getFields(): Record<string, string>

    parse(deck:string, url:string = "", frozen_fields_dict: Record<string, Record<string, string>> = {}): NOTE_AND_ID {
        let template = JSON.parse(JSON.stringify(NOTE_DICT_TEMPLATE))
        template["modelName"] = this.note_type
        template["fields"] = this.getFields()
        if (url) {
            this.formatter.format_note_with_url(template, url)
        }
        if (Object.keys(frozen_fields_dict).length) {
            this.formatter.format_note_with_frozen_fields(template, frozen_fields_dict)
        }

        template["tags"].push(...this.tags)
        template["deckName"] = deck
        return {note: template, identifier: this.identifier}
    }

}

export class Note extends AbstractNote {

    getSplitText(): string[] {
        return this.text.split("\n")
    }

    getIdentifier(): number | null {
        if (this.ID_REGEXP.test(this.split_text[this.split_text.length-1])) {
            return parseInt(this.ID_REGEXP.exec(this.split_text.pop())[1])
        } else {
            return null
        }
    }

    getTags(): string[] {
        if (this.split_text[this.split_text.length-1].startsWith(TAG_PREFIX)) {
            return this.split_text.pop().slice(TAG_PREFIX.length).split(TAG_SEP)
        } else {
            return []
        }
    }

    getNoteType(): string {
        return this.split_text[0]
    }

    fieldFromLine(line: string): [string, string] {
        /*From a given line, determine the next field to add text into.

        Then, return the stripped line, and the field.*/
        for (let field of this.field_names) {
            if (line.startsWith(field + ":")) {
                return [line.slice((field + ":").length), field]
            }
        }
        return [line,this.current_field]
    }

    getFields(): Record<string, string> {
        let fields: Record<string, string> = {}
        for (let field of this.field_names) {
            fields[field] = ""
        }
        for (let line of this.split_text.slice(1)) {
            [line, this.current_field] = this.fieldFromLine(line)
            fields[this.current_field] += line + "\n"
        }
        for (let key in fields) {
            fields[key] = this.formatter.format(
                fields[key].trim(),
                this.note_type.includes("Cloze") && this.curly_cloze
            ).trim()
        }
        return fields
    }

}

export class InlineNote extends AbstractNote {

    static TAG_REGEXP: RegExp = /Tags: (.*)/;
    static ID_REGEXP: RegExp = /(?:<!--)?ID: (\d+)/;
    static TYPE_REGEXP: RegExp = /\[(.*?)\]/;

    getSplitText(): string[] {
        return this.text.split(" ")
    }

    getIdentifier(): number | null {
        const result = this.text.match(InlineNote.ID_REGEXP)
        if (result) {
            this.text = this.text.slice(0,result.index).trim()
            return parseInt(result[1])
        } else {
            return null
        }
    }

    getTags(): string[] {
        const result = this.text.match(InlineNote.TAG_REGEXP)
        if (result) {
            this.text = this.text.slice(0, result.index).trim()
            return result[1].split(TAG_SEP)
        } else {
            return []
        }
    }

    getNoteType(): string {
        const result = this.text.match(InlineNote.TYPE_REGEXP)
        this.text = this.text.slice(result.index + result[0].length)
        return result[1]
    }

    getFields(): Record<string, string> {
        let fields: Record<string, string> = {}
        for (let field of this.field_names) {
            fields[field] = ""
        }
        for (let word of this.text.split(" ")) {
            for (let field of this.field_names) {
                if (word === field + ":") {
                    this.current_field = field
                    word = ""
                }
            }
            fields[this.current_field] += word + " "
        }
        for (let key in fields) {
            fields[key] = this.formatter.format(
                fields[key].trim(),
                this.note_type.includes("Cloze") && this.curly_cloze
            ).trim()
        }
        return fields
    }


}

export class RegexNote {
	ID_REGEXP_STR: string = String.raw`\n?(?:<!--)?(?:ID: (\d+).*)`
	TAG_REGEXP_STR: string = String.raw`(Tags: .*)`

	match: RegExpMatchArray
	note_type: string
	groups: Array<string>
	identifier: number | null
	tags: string[]
    field_names: string[]
	curly_cloze: boolean
	formatter: FormatConverter

	constructor(
			match: RegExpMatchArray,
			note_type: string,
			FIELDS_DICT: Record<string, string[]>,
			tags: boolean = false,
			id: boolean = false,
			curly_cloze:boolean = false
	) {
		this.match = match
		this.note_type = note_type
		this.identifier = id ? parseInt(this.match.pop()) : null
		this.tags = tags ? this.match.pop().slice(TAG_PREFIX.length).split(TAG_SEP) : []
		this.field_names = FIELDS_DICT[note_type]
		this.curly_cloze = curly_cloze
		this.formatter = new FormatConverter()
	}

	getFields(): Record<string, string> {
		let fields: Record<string, string> = {}
        for (let field of this.field_names) {
            fields[field] = ""
        }
		for (let index in this.match) {
			fields[this.field_names[index]] = this.match[index]
		}
		for (let key in fields) {
            fields[key] = this.formatter.format(
                fields[key].trim(),
                this.note_type.includes("Cloze") && this.curly_cloze
            ).trim()
        }
        return fields
	}

	parse(deck: string, url: string = "", frozen_fields_dict: Record<string, Record<string, string>>): NOTE_AND_ID {
		let template = JSON.parse(JSON.stringify(NOTE_DICT_TEMPLATE))
		template["modelName"] = this.note_type
		template["fields"] = this.getFields()
		if (url) {
            this.formatter.format_note_with_url(template, url)
        }
        if (Object.keys(frozen_fields_dict).length) {
            this.formatter.format_note_with_frozen_fields(template, frozen_fields_dict)
        }
		if (this.note_type.includes("Cloze") && !note_has_clozes(template)) {
			this.identifier = 42 //An error code that says "don't add this note!"
		}
		return {note: template, identifier: this.identifier}
	}
}
