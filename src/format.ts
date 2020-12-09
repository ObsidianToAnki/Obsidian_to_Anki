import { NOTE } from './interfaces/note'
import { basename } from 'path'
import { bytesToBase64 } from 'byte-base64'
import { App } from 'obsidian'
import { Converter } from 'showdown'

let converter: Converter = new Converter()

let OBS_INLINE_MATH_REGEXP: RegExp = /(?<!\$)\$((?=[\S])(?=[^$])[\s\S]*?\S)\$/g
let OBS_DISPLAY_MATH_REGEXP: RegExp = /\$\$([\s\S]*?)\$\$/g
let OBS_CODE_REGEXP:RegExp = /(?<!`)`(?=[^`])[\s\S]*?`/g
let OBS_DISPLAY_CODE_REGEXP:RegExp = /```[\s\S]*?```/g

let ANKI_MATH_REGEXP:RegExp = /(\\\[[\s\S]*?\\\])|(\\\([\s\S]*?\\\))/g

let MATH_REPLACE:string = "OBSTOANKIMATH"
let INLINE_CODE_REPLACE:string = "OBSTOANKICODEINLINE"
let DISPLAY_CODE_REPLACE:string = "OBSTOANKICODEDISPLAY"

let IMAGE_REGEXP:RegExp = /<img alt=".*?" src="(.*?)"/g
let SOUND_REGEXP:RegExp = /\[sound:(.+)\]/g
let CLOZE_REGEXP:RegExp = /(?:(?<!{){(?:c?(\d+)[:|])?(?!{))((?:[^\n][\n]?)+?)(?:(?<!})}(?!}))/g
let URL_REGEXP:RegExp = /https?:\/\//g

let PARA_OPEN:string = "<p>"
let PARA_CLOSE:string = "</p>"

export class FormatConverter {

	cloze_unset_num:number = 1
    media_to_add = {}
    ADDED_MEDIA: string[] = []
    app: App

    constructor(app: App, ADDED_MEDIA: string[] = []) {
        this.ADDED_MEDIA = ADDED_MEDIA
        this.app = app
    }

	format_note_with_url(note: NOTE, url: string): void {
		for (let field in note.fields) {
			note.fields[field] += '<br><a href="' + url + '" class="obsidian-link">Obsidian</a>'
		}
	}

	format_note_with_frozen_fields(note: NOTE, frozen_fields_dict: Record<string, Record<string, string>>): void {
		for (let field in note.fields) {
			note.fields[field] += frozen_fields_dict[note.modelName][field]
		}
	}

	obsidian_to_anki_math(note_text: string): string {
		return note_text.replace(
				OBS_DISPLAY_MATH_REGEXP, "\\[$1\\]"
		).replace(
			OBS_INLINE_MATH_REGEXP,
			"\\($1\\)"
		)
	}

	cloze_repl(_1: string, match_id: string, match_content: string): string {
		if (match_id == undefined) {
			let result = "{{c" + this.cloze_unset_num.toString() + "::" + match_content + "}}"
			this.cloze_unset_num += 1
			return result
		}
		let result = "{{c" + match_id + "::" + match_content + "}}"
		return result
	}

	curly_to_cloze(text: string): string {
		/*Change text in curly brackets to Anki-formatted cloze.*/
		text = text.replaceAll(CLOZE_REGEXP, this.cloze_repl)
		this.cloze_unset_num = 1
		return text
	}

	is_url(text: string): boolean {
		/*Check whether text looks like a url.*/
		return URL_REGEXP.test(text)
	}

	async get_images(html_text: string) {
        /*Get all the images that need to be added.*/
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
        /*Get all the audio that needs to be added.*/
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
		[note_text, inline_code_matches] = this.censor(note_text, OBS_CODE_REGEXP, INLINE_CODE_REPLACE);
		[note_text, display_code_matches] = this.censor(note_text, OBS_DISPLAY_CODE_REGEXP, DISPLAY_CODE_REPLACE)
		if (cloze) {
			note_text = this.curly_to_cloze(note_text)
		}
		note_text = this.decensor(note_text, INLINE_CODE_REPLACE, inline_code_matches)
		note_text = this.decensor(note_text, DISPLAY_CODE_REPLACE, display_code_matches)
		note_text = converter.makeHtml(note_text)
		note_text = this.decensor(note_text, MATH_REPLACE, math_matches)
		this.get_images(note_text)
		this.get_audio(note_text)
		note_text = note_text.trim()
		// Remove unnecessary paragraph tag
		if (note_text.startsWith(PARA_OPEN) && note_text.endsWith(PARA_CLOSE)) {
			note_text = note_text.slice(PARA_OPEN.length, -1 * PARA_CLOSE.length)
		}
		return note_text
	}




}
