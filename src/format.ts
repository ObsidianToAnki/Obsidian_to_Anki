import { AnkiConnectNote } from './interfaces/note-interface'
import { basename } from 'path'
import { bytesToBase64 } from 'byte-base64'
import { Converter } from 'showdown'
import { CachedMetadata } from 'obsidian'
import * as c from './constants'

const ANKI_MATH_REGEXP:RegExp = /(\\\[[\s\S]*?\\\])|(\\\([\s\S]*?\\\))/g

const MATH_REPLACE:string = "OBSTOANKIMATH"
const INLINE_CODE_REPLACE:string = "OBSTOANKICODEINLINE"
const DISPLAY_CODE_REPLACE:string = "OBSTOANKICODEDISPLAY"

const IMAGE_REGEXP:RegExp = /<img alt=".*?" src="(.*?)"/g
const SOUND_REGEXP:RegExp = /\[sound:(.+)\]/g
const CLOZE_REGEXP:RegExp = /(?:(?<!{){(?:c?(\d+)[:|])?(?!{))((?:[^\n][\n]?)+?)(?:(?<!})}(?!}))/g
const URL_REGEXP:RegExp = /https?:\/\//g

const PARA_OPEN:string = "<p>"
const PARA_CLOSE:string = "</p>"

let cloze_unset_num: number = 1

let converter: Converter = new Converter()

export class FormatConverter {

	file_cache: CachedMetadata

	constructor(file_cache: CachedMetadata) {
		this.file_cache = file_cache
	}

	format_note_with_url(note: AnkiConnectNote, url: string): void {
		for (let field in note.fields) {
			note.fields[field] += '<br><a href="' + url + '" class="obsidian-link">Obsidian</a>'
		}
	}

	format_note_with_frozen_fields(note: AnkiConnectNote, frozen_fields_dict: Record<string, Record<string, string>>): void {
		for (let field in note.fields) {
			note.fields[field] += frozen_fields_dict[note.modelName][field]
		}
	}

	obsidian_to_anki_math(note_text: string): string {
		return note_text.replace(
				c.OBS_DISPLAY_MATH_REGEXP, "\\[$1\\]"
		).replace(
			c.OBS_INLINE_MATH_REGEXP,
			"\\($1\\)"
		)
	}

	cloze_repl(_1: string, match_id: string, match_content: string): string {
		if (match_id == undefined) {
			let result = "{{c" + cloze_unset_num.toString() + "::" + match_content + "}}"
			cloze_unset_num += 1
			return result
		}
		let result = "{{c" + match_id + "::" + match_content + "}}"
		return result
	}

	curly_to_cloze(text: string): string {
		/*Change text in curly brackets to Anki-formatted cloze.*/
		text = text.replaceAll(CLOZE_REGEXP, this.cloze_repl)
		cloze_unset_num = 1
		return text
	}

	is_url(text: string): boolean {
		/*Check whether text looks like a url.*/
		return URL_REGEXP.test(text)
	}

	/*
	async get_images(html_text: string) {
        //Get all the images that need to be added.
		for (let match of html_text.matchAll(IMAGE_REGEXP)) {
			let path = match[1]
			if (this.is_url(path)) {
				continue
				//Skips over web-based images
			}
			path = decodeURI(path)
			let filename = basename(path)
            if (!this.ADDED_MEDIA.includes(filename) && !Object.keys(this.media_to_add).includes(filename)) {
                this.media_to_add[filename] = bytesToBase64(
                    new Uint8Array(
                        await this.app.vault.adapter.readBinary(path)
                    )
                )
            }
		}
	}

    async get_audio(html_text: string) {
        //Get all the audio that needs to be added.
        for (let match of html_text.matchAll(SOUND_REGEXP)) {
            let path = match[1]
            let filename = basename(path)
            if (!this.ADDED_MEDIA.includes(filename) && !Object.keys(this.media_to_add).includes(filename)) {
                this.media_to_add[filename] = bytesToBase64(
                    new Uint8Array(
                        await this.app.vault.adapter.readBinary(path)
                    )
                )
            }
        }
    }
	*/

    path_to_filename(match: string, path: string): string {
		/*Replace the src in match appropriately.*/
		if (this.is_url(path)) {
			return match //Don't alter urls!
		}
		path = decodeURI(path)
		match.replace(path, basename(path))
		return match
    }

	fix_image_src(html_text: string): string {
		return html_text.replace(IMAGE_REGEXP, this.path_to_filename)
	}

	fix_audio_src(html_text: string): string {
		return html_text.replace(SOUND_REGEXP, this.path_to_filename)
	}

	censor(note_text: string, regexp: RegExp, mask: string): [string, string[]] {
		/*Take note_text and replace every match of regexp with mask, simultaneously adding it to a string array*/
		let matches: string[] = []
		for (let match of note_text.matchAll(regexp)) {
			matches.push(match[0])
		}
		return [note_text.replaceAll(regexp, mask), matches]
	}

	decensor(note_text: string, mask:string, replacements: string[]): string {
		for (let replacement of replacements) {
			note_text = note_text.replace(
				mask, replacement
			)
		}
		return note_text
	}

	format(note_text: string, cloze: boolean = false): string {
		note_text = this.obsidian_to_anki_math(note_text)
		//Extract the parts that are anki math
		let math_matches: string[]
		let inline_code_matches: string[]
		let display_code_matches: string[]
		[note_text, math_matches] = this.censor(note_text, ANKI_MATH_REGEXP, MATH_REPLACE);
		[note_text, inline_code_matches] = this.censor(note_text, c.OBS_CODE_REGEXP, INLINE_CODE_REPLACE);
		[note_text, display_code_matches] = this.censor(note_text, c.OBS_DISPLAY_CODE_REGEXP, DISPLAY_CODE_REPLACE)
		if (cloze) {
			note_text = this.curly_to_cloze(note_text)
		}
		note_text = this.decensor(note_text, INLINE_CODE_REPLACE, inline_code_matches)
		note_text = this.decensor(note_text, DISPLAY_CODE_REPLACE, display_code_matches)
		note_text = converter.makeHtml(note_text)
		note_text = this.decensor(note_text, MATH_REPLACE, math_matches).trim()
		/* Need to figure out another way to do this
		this.get_images(note_text)
		this.get_audio(note_text)
		*/
		// Remove unnecessary paragraph tag
		if (note_text.startsWith(PARA_OPEN) && note_text.endsWith(PARA_CLOSE)) {
			note_text = note_text.slice(PARA_OPEN.length, -1 * PARA_CLOSE.length)
		}
		return note_text
	}




}
