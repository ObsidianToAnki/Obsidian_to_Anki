import { NOTE } from './interfaces/note'
import { basename } from 'path'
import { bytesToBase64 } from 'byte-base64'
import { App } from 'obsidian'

let OBS_INLINE_MATH_REGEXP: RegExp = /(?<!\$)\$((?=[\S])(?=[^$])[\s\S]*?\S)\$/g
let OBS_DISPLAY_MATH_REGEXP: RegExp = /\$\$([\s\S]*?)\$\$/g
let OBS_CODE_REGEXP:RegExp = /(?<!`)`(?=[^`])[\s\S]*?`/g
let OBS_DISPLAY_CODE_REGEXP:RegExp = /```[\s\S]*?```/g

let ANKI_MATH_REGEXP:RegExp = /(\\\[[\s\S]*?\\\])|(\\\([\s\S]*?\\\))/g

let MATH_REPLACE:string = "OBSTOANKIMATH"

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

	format_note_with_frozen_fields(note: NOTE, frozen_fields_dict): void {
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

	cloze_repl(match: string, match_id: string, match_content: string): string {
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




}
