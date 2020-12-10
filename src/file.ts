/*Performing script operations on markdown file contents*/

import { FIELDS_DICT, FROZEN_FIELDS_DICT } from './interfaces/field-interface'
import { Note, InlineNote, CLOZE_ERROR, TAG_SEP } from './note'
import { AnkiConnectNote, AnkiConnectNoteAndID } from './interfaces/note-interface'
import { Md5 } from 'ts-md5/dist/md5';
import * as AnkiConnect from './anki'

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

interface ExternalAppData {
    file_contents: string
    path: string
    vault_name: string
    fields_dict: FIELDS_DICT
    frozen_fields_dict: FROZEN_FIELDS_DICT

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
}

abstract class AbstractFile {
    file: string
    url: string
    original_file: string
    data: ExternalAppData

    frozen_fields_dict: FROZEN_FIELDS_DICT
    target_deck: string
    global_tags: string

    notes_to_add: AnkiConnectNote[]
    id_indexes: number[]
    notes_to_edit: AnkiConnectNoteAndID[]
    notes_to_delete: number[]
    all_notes_to_add: AnkiConnectNote[]

    note_ids: number[]
    card_ids: number[]
    tags: string[]

    constructor(data: ExternalAppData) {
        this.data = data
        this.file = data.file_contents
        this.url = data.add_file_link ? "obsidian://open?vault=" + encodeURIComponent(data.vault_name) + "&file=" + encodeURIComponent(data.path) : ""
        this.original_file = this.file
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
            const parsed_fields: Record<string, string> = new Note(virtual_note, this.data.fields_dict, this.data.curly_cloze).getFields()
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

    setNoteIDs(note_ids: number[]) {
        this.note_ids = note_ids
    }

    removeEmpties() {
        this.file = this.file.replaceAll(this.data.EMPTY_REGEXP, "")
    }

}

export class File {
    file: string
    url: string
    original_file: string
    data: ExternalAppData

    frozen_fields_dict: FROZEN_FIELDS_DICT
    target_deck: string
    global_tags: string

    notes_to_add: AnkiConnectNote[]
    id_indexes: number[]
    notes_to_edit: AnkiConnectNoteAndID[]
    notes_to_delete: number[]
    inline_notes_to_add: AnkiConnectNote[]
    inline_id_indexes: number[]
    all_notes_to_add: AnkiConnectNote[]

    note_ids: number[]
    card_ids: number[]
    tags: string[]

    constructor(data: ExternalAppData) {
        this.data = data
        this.file = data.file_contents
        this.url = data.add_file_link ? "obsidian://open?vault=" + encodeURIComponent(data.vault_name) + "&file=" + encodeURIComponent(data.path) : ""
        this.original_file = this.file
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
            const parsed_fields: Record<string, string> = new Note(virtual_note, this.data.fields_dict, this.data.curly_cloze).getFields()
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
            const [note, position]: [string, number] = [note_match[1], note_match[0].indexOf(note_match[1]) + note_match[1].length]
            // That second thing essentially gets the index of the end of the first capture group.
            const parsed = new Note(
                note, this.data.fields_dict, this.data.curly_cloze
            ).parse(
                this.target_deck, this.url, this.frozen_fields_dict
            )
            if (parsed.identifier == null) {
                // Need to make sure global_tags get added
                parsed.note.tags.push(...this.global_tags.split(TAG_SEP))
                this.notes_to_add.push(parsed.note)
                this.id_indexes.push(position)
            } else if (!this.data.EXISTING_IDS.includes(parsed.identifier)) {
                // Need to show an error
                console.log("Warning! note with id", parsed.identifier, " in file ", this.data.path, " does not exist in Anki!")
            } else {
                this.notes_to_edit.push(parsed)
            }
        }
    }

    scanInlineNotes() {
        for (let note_match of this.file.matchAll(this.data.INLINE_REGEXP)) {
            const [note, position]: [string, number] = [note_match[1], note_match[0].indexOf(note_match[1]) + note_match[1].length]
            // That second thing essentially gets the index of the end of the first capture group.
            const parsed = new InlineNote(
                note, this.data.fields_dict, this.data.curly_cloze
            ).parse(
                this.target_deck, this.url, this.frozen_fields_dict
            )
            if (parsed.identifier == null) {
                // Need to make sure global_tags get added
                parsed.note.tags.push(...this.global_tags.split(TAG_SEP))
                this.inline_notes_to_add.push(parsed.note)
                this.inline_id_indexes.push(position)
            } else if (!this.data.EXISTING_IDS.includes(parsed.identifier)) {
                // Need to show an error
                console.log("Warning! note with id", parsed.identifier, " in file ", this.data.path, " does not exist in Anki!")
            } else {
                this.notes_to_edit.push(parsed)
            }
        }
    }

    scanDeletions() {
        for (let match of this.file.matchAll(this.data.EMPTY_REGEXP)) {
            this.notes_to_delete.push(parseInt(match[1]))
        }
    }

    scanFile() {
        this.setupScan()
        this.scanNotes()
        this.scanInlineNotes()
        this.all_notes_to_add = this.notes_to_add.concat(this.inline_notes_to_add)
        this.scanDeletions()
    }

    setNoteIDs(note_ids: number[]) {
        this.note_ids = note_ids
    }

    writeIDs() {
        let normal_inserts: [number, string][] = []
        for (let i in this.id_indexes) {
            const id_position = this.id_indexes[i]
            const identifier = this.note_ids[i]
            if (identifier) {
                normal_inserts.push([id_position, id_to_str(identifier, false, this.data.comment)])
            }
        }
        let inline_inserts: [number, string][] = []
        for (let i in this.inline_id_indexes) {
            const id_position = this.inline_id_indexes[i]
            const identifier = this.note_ids[i + this.notes_to_add.length] //Since the initial part is all regular notes, then final part is inline notes
            if (identifier) {
                inline_inserts.push([id_position, id_to_str(identifier, true, this.data.comment)])
            }
        }
        this.file = string_insert(this.file, normal_inserts.concat(inline_inserts))
    }

    removeEmpties() {
        this.file = this.file.replaceAll(this.data.EMPTY_REGEXP, "")
    }

    getAddNotes(): AnkiConnect.AnkiConnectRequest {
        let actions: AnkiConnect.AnkiConnectRequest[] = []
        for (let note of this.notes_to_add) {
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

    setCardIDs(card_ids: number[]) {
        this.card_ids = card_ids
    }

    getChangeDecks(): AnkiConnect.AnkiConnectRequest {
        return AnkiConnect.changeDeck(this.card_ids, this.target_deck)
    }

    setTags(tags: string[]) {
        this.tags = tags
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
