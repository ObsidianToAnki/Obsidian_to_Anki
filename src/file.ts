/*Performing script operations on markdown file contents*/

import { FROZEN_FIELDS_DICT } from './interfaces/field-interface'
import { AnkiConnectNote, AnkiConnectNoteAndID } from './interfaces/note-interface'
import { FileData } from './interfaces/settings-interface'
import { Note, InlineNote, RegexNote, CLOZE_ERROR, TAG_SEP, ID_REGEXP_STR, TAG_REGEXP_STR } from './note'
import { Md5 } from 'ts-md5/dist/md5';
import * as AnkiConnect from './anki'
import * as c from './constants'
import { FormatConverter } from './format'
import { CachedMetadata } from 'obsidian'

const double_regexp: RegExp = /(?:\r\n|\r|\n)((?:\r\n|\r|\n)(?:<!--)?ID: \d+)/

function id_to_str(identifier:number, inline:boolean = false, comment:boolean = false): string {
    let result = "ID: " + identifier.toString()
    if (comment) {
        result = "<!--" + result + "-->"
    }
    if (inline) {
        result += " "
    } else {
        result += "\n"
    }
    return result
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
			[match.index, match.index + match[0].length]
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
		if (!(contained_in([match.index, match.index + match[0].length], ignore_spans))) {
			yield match
		}
	}
}

abstract class AbstractFile {
    file: string
    path: string
    url: string
    original_file: string
    data: FileData

    frozen_fields_dict: FROZEN_FIELDS_DICT
    target_deck: string
    global_tags: string

    notes_to_add: AnkiConnectNote[]
    id_indexes: number[]
    notes_to_edit: AnkiConnectNoteAndID[]
    notes_to_delete: number[]
    all_notes_to_add: AnkiConnectNote[]

    note_ids: Array<number | null>
    card_ids: number[]
    tags: string[]

    formatter: FormatConverter

    constructor(file_contents: string, path:string, url: string, data: FileData, file_cache: CachedMetadata) {
        this.data = data
        this.file = file_contents
        this.path = path
        this.url = url
        this.original_file = this.file
        this.formatter = new FormatConverter(file_cache, this.data.vault_name)
    }

    setup_frozen_fields_dict() {
        let frozen_fields_dict: FROZEN_FIELDS_DICT = {}
        for (let note_type in this.data.fields_dict) {
            let fields: string[] = this.data.fields_dict[note_type]
            let temp_dict: Record<string, string> = {}
            for (let field of fields) {
                temp_dict[field] = ""
            }
            frozen_fields_dict[note_type] = temp_dict
        }
        for (let match of this.file.matchAll(this.data.FROZEN_REGEXP)) {
            const [note_type, fields]: [string, string] = [match[1], match[2]]
            const virtual_note = note_type + "\n" + fields
            const parsed_fields: Record<string, string> = new Note(virtual_note, this.data.fields_dict, this.data.curly_cloze, this.formatter).getFields()
            frozen_fields_dict[note_type] = parsed_fields
        }
        this.frozen_fields_dict = frozen_fields_dict
    }

    setup_target_deck() {
        const result = this.file.match(this.data.DECK_REGEXP)
        this.target_deck = result ? result[1] : this.data.template["deckName"]
    }

    setup_global_tags() {
        const result = this.file.match(this.data.TAG_REGEXP)
        this.global_tags = result ? result[1] : ""
    }

    getHash(): string {
        return Md5.hashStr(this.file) as string
    }

    abstract scanFile(): void

    scanDeletions() {
        for (let match of this.file.matchAll(this.data.EMPTY_REGEXP)) {
            this.notes_to_delete.push(parseInt(match[1]))
        }
    }

    abstract writeIDs(): void

    removeEmpties() {
        this.file = this.file.replaceAll(this.data.EMPTY_REGEXP, "")
    }

    getAddNotes(): AnkiConnect.AnkiConnectRequest {
        let actions: AnkiConnect.AnkiConnectRequest[] = []
        for (let note of this.all_notes_to_add) {
            actions.push(AnkiConnect.addNote(note))
        }
        return AnkiConnect.multi(actions)
    }

    getDeleteNotes(): AnkiConnect.AnkiConnectRequest {
        return AnkiConnect.deleteNotes(this.notes_to_delete)
    }

    getUpdateFields(): AnkiConnect.AnkiConnectRequest {
        let actions: AnkiConnect.AnkiConnectRequest[] = []
        for (let parsed of this.notes_to_edit) {
            actions.push(
                AnkiConnect.updateNoteFields(
                    parsed.identifier, parsed.note.fields
                )
            )
        }
        return AnkiConnect.multi(actions)
    }

    getNoteInfo(): AnkiConnect.AnkiConnectRequest {
        let IDs: number[] = []
        for (let parsed of this.notes_to_edit) {
            IDs.push(parsed.identifier)
        }
        return AnkiConnect.notesInfo(IDs)
    }

    getChangeDecks(): AnkiConnect.AnkiConnectRequest {
        return AnkiConnect.changeDeck(this.card_ids, this.target_deck)
    }

    getClearTags(): AnkiConnect.AnkiConnectRequest {
        let IDs: number[] = []
        for (let parsed of this.notes_to_edit) {
            IDs.push(parsed.identifier)
        }
        return AnkiConnect.removeTags(IDs, this.tags.join(" "))
    }

    getAddTags(): AnkiConnect.AnkiConnectRequest {
        let actions: AnkiConnect.AnkiConnectRequest[] = []
        for (let parsed of this.notes_to_edit) {
            actions.push(
                AnkiConnect.addTags([parsed.identifier], parsed.note.tags.join(" ") + " " + this.global_tags)
            )
        }
        return AnkiConnect.multi(actions)
    }

}

export class File extends AbstractFile {

    inline_notes_to_add: AnkiConnectNote[]
    inline_id_indexes: number[]

    setupScan() {
        this.setup_frozen_fields_dict()
        this.setup_target_deck()
        this.setup_global_tags()
        this.notes_to_add = []
        this.id_indexes = []
        this.notes_to_edit = []
        this.notes_to_delete = []
        this.inline_notes_to_add = []
        this.inline_id_indexes = []
    }

    scanNotes() {
        for (let note_match of this.file.matchAll(this.data.NOTE_REGEXP)) {
            let [note, position]: [string, number] = [note_match[1], note_match.index + note_match[0].indexOf(note_match[1]) + note_match[1].length]
            // That second thing essentially gets the index of the end of the first capture group.
            let parsed = new Note(
                note, this.data.fields_dict, this.data.curly_cloze, this.formatter
            ).parse(
                this.target_deck, this.url, this.frozen_fields_dict, this.data.file_link_fields
            )
            if (parsed.identifier == null) {
                // Need to make sure global_tags get added
                parsed.note.tags.push(...this.global_tags.split(TAG_SEP))
                this.notes_to_add.push(parsed.note)
                this.id_indexes.push(position)
            } else if (!this.data.EXISTING_IDS.includes(parsed.identifier)) {
                // Need to show an error
                console.log("Warning! note with id", parsed.identifier, " in file ", this.path, " does not exist in Anki!")
            } else {
                this.notes_to_edit.push(parsed)
            }
        }
    }

    scanInlineNotes() {
        for (let note_match of this.file.matchAll(this.data.INLINE_REGEXP)) {
            let [note, position]: [string, number] = [note_match[1], note_match.index + note_match[0].indexOf(note_match[1]) + note_match[1].length]
            // That second thing essentially gets the index of the end of the first capture group.
            let parsed = new InlineNote(
                note, this.data.fields_dict, this.data.curly_cloze, this.formatter
            ).parse(
                this.target_deck, this.url, this.frozen_fields_dict, this.data.file_link_fields
            )
            if (parsed.identifier == null) {
                // Need to make sure global_tags get added
                parsed.note.tags.push(...this.global_tags.split(TAG_SEP))
                this.inline_notes_to_add.push(parsed.note)
                this.inline_id_indexes.push(position)
            } else if (!this.data.EXISTING_IDS.includes(parsed.identifier)) {
                // Need to show an error
                console.log("Warning! note with id", parsed.identifier, " in file ", this.path, " does not exist in Anki!")
            } else {
                this.notes_to_edit.push(parsed)
            }
        }
    }

    scanFile() {
        this.setupScan()
        this.scanNotes()
        this.scanInlineNotes()
        this.all_notes_to_add = this.notes_to_add.concat(this.inline_notes_to_add)
        this.scanDeletions()
    }

    writeIDs() {
        let normal_inserts: [number, string][] = []
        this.id_indexes.forEach(
            (id_position: number, index: number) => {
                const identifier: number | null = this.note_ids[index]
                if (identifier) {
                    normal_inserts.push([id_position, id_to_str(identifier, false, this.data.comment)])
                }
            }
        )
        let inline_inserts: [number, string][] = []
        this.inline_id_indexes.forEach(
            (id_position: number, index: number) => {
                const identifier: number | null = this.note_ids[index + this.notes_to_add.length] //Since the initial part is all regular notes, then final part is inline notes
                if (identifier) {
                    inline_inserts.push([id_position, id_to_str(identifier, true, this.data.comment)])
                }
            }
        )
        this.file = string_insert(this.file, normal_inserts.concat(inline_inserts))
    }

}

export class RegexFile extends AbstractFile {

    ignore_spans: [number, number][]
    custom_regexps: Record<string, string>

    constructor(file_contents: string, path:string, url: string, data: FileData, file_cache: CachedMetadata) {
        super(file_contents, path, url, data, file_cache)
        this.custom_regexps = data.custom_regexps
    }

    add_spans_to_ignore() {
        this.ignore_spans = []
        this.ignore_spans.push(...spans(this.data.NOTE_REGEXP, this.file))
        this.ignore_spans.push(...spans(this.data.INLINE_REGEXP, this.file))
        this.ignore_spans.push(...spans(c.OBS_INLINE_MATH_REGEXP, this.file))
        this.ignore_spans.push(...spans(c.OBS_DISPLAY_MATH_REGEXP, this.file))
        this.ignore_spans.push(...spans(c.OBS_CODE_REGEXP, this.file))
        this.ignore_spans.push(...spans(c.OBS_DISPLAY_CODE_REGEXP, this.file))
    }

    setupScan() {
        this.setup_frozen_fields_dict()
        this.setup_target_deck()
        this.setup_global_tags()
        this.add_spans_to_ignore()
        this.notes_to_add = []
        this.id_indexes = []
        this.notes_to_edit = []
        this.notes_to_delete = []
    }

    scanFile() {
        this.setupScan()
        for (let note_type in this.custom_regexps) {
            const regexp_str: string = this.custom_regexps[note_type]
            if (regexp_str) {
                this.search(note_type, regexp_str)
            }
        }
        this.all_notes_to_add = this.notes_to_add
        this.scanDeletions()
    }

    search(note_type: string, regexp_str: string) {
        //Search the file for regex matches of this type,
        //ignoring matches inside ignore_spans,
        //and adding any matches to ignore_spans.
        this.search_tags_id(note_type, regexp_str)
        this.search_id(note_type, regexp_str)
        this.search_tags(note_type, regexp_str)
        this.search_none(note_type, regexp_str)
    }

    search_tags_id(note_type: string, regexp_str: string) {
        const regexp: RegExp = new RegExp(regexp_str + TAG_REGEXP_STR + ID_REGEXP_STR, 'gm')
        for (let match of findignore(regexp, this.file, this.ignore_spans)) {
            this.ignore_spans.push([match.index, match.index + match[0].length])
            const parsed: AnkiConnectNoteAndID = new RegexNote(
                match, note_type, this.data.fields_dict,
                true, true, this.data.curly_cloze, this.formatter
            ).parse(this.target_deck,this.url,this.frozen_fields_dict, this.data.file_link_fields)
            if (!this.data.EXISTING_IDS.includes(parsed.identifier)) {
                console.log("Warning! Note with id", parsed.identifier, " in file ", this.path, " does not exist in Anki!")
            } else {
                this.notes_to_edit.push(parsed)
            }
        }
    }

    search_id(note_type: string, regexp_str: string) {
        const regexp: RegExp = new RegExp(regexp_str + ID_REGEXP_STR, 'gm')
        for (let match of findignore(regexp, this.file, this.ignore_spans)) {
            this.ignore_spans.push([match.index, match.index + match[0].length])
            const parsed: AnkiConnectNoteAndID = new RegexNote(
                match, note_type, this.data.fields_dict,
                false, true, this.data.curly_cloze, this.formatter
            ).parse(this.target_deck, this.url, this.frozen_fields_dict, this.data.file_link_fields)
            if (!this.data.EXISTING_IDS.includes(parsed.identifier)) {
                console.log("Warning! Note with id", parsed.identifier, " in file ", this.path, " does not exist in Anki!")
            } else {
                this.notes_to_edit.push(parsed)
            }
        }
    }

    search_tags(note_type: string, regexp_str: string) {
        const regexp: RegExp = new RegExp(regexp_str + TAG_REGEXP_STR, 'gm')
        for (let match of findignore(regexp, this.file, this.ignore_spans)) {
            this.ignore_spans.push([match.index, match.index + match[0].length])
            const parsed: AnkiConnectNoteAndID = new RegexNote(
                match, note_type, this.data.fields_dict,
                true, false, this.data.curly_cloze, this.formatter
            ).parse(this.target_deck, this.url, this.frozen_fields_dict, this.data.file_link_fields)
            if (parsed.identifier == CLOZE_ERROR) {
                continue
            }
            parsed.note.tags.push(...this.global_tags.split(TAG_SEP))
            this.notes_to_add.push(parsed.note)
            this.id_indexes.push(match.index + match[0].length)
        }
    }

    search_none(note_type: string, regexp_str: string) {
        const regexp: RegExp = new RegExp(regexp_str, 'gm')
        for (let match of findignore(regexp, this.file, this.ignore_spans)) {
            this.ignore_spans.push([match.index, match.index + match[0].length])
            const parsed: AnkiConnectNoteAndID = new RegexNote(
                match, note_type, this.data.fields_dict,
                false, false, this.data.curly_cloze, this.formatter
            ).parse(this.target_deck, this.url, this.frozen_fields_dict, this.data.file_link_fields)
            if (parsed.identifier == CLOZE_ERROR) {
                console.log("Note has no cloze deletions!")
                continue
            }
            parsed.note.tags.push(...this.global_tags.split(TAG_SEP))
            this.notes_to_add.push(parsed.note)
            this.id_indexes.push(match.index + match[0].length)
        }
    }

    fix_newline_ids() {
        this.file = this.file.replaceAll(double_regexp, "$1")
    }

    writeIDs() {
        let inserts: [number, string][] = []
        this.id_indexes.forEach(
            (id_position: number, index: number) => {
                const identifier: number | null = this.note_ids[index]
                if (identifier) {
                    inserts.push([id_position, id_to_str(identifier, false, this.data.comment)])
                }
            }
        )
        this.file = string_insert(this.file, inserts)
        this.fix_newline_ids()
    }


}
