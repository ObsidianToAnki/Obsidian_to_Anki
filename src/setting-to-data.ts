import { PluginSettings, ParsedSettings } from './interfaces/settings-interface'
import { App } from 'obsidian'
import * as AnkiConnect from './anki'
import { ID_REGEXP_STR } from './note'
import { escapeRegex } from './constants'

export async function settingToData(app: App, settings: PluginSettings, fields_dict: Record<string, string[]>): Promise<ParsedSettings> {
    let result: ParsedSettings = <ParsedSettings>{}

    //Some processing required
    result.vault_name = app.vault.getName()
    result.fields_dict = fields_dict
    result.custom_regexps = settings.CUSTOM_REGEXPS
    result.file_link_fields = settings.FILE_LINK_FIELDS
    result.context_fields = settings.CONTEXT_FIELDS
    result.folder_decks = settings.FOLDER_DECKS
    result.folder_tags = settings.FOLDER_TAGS
    result.template = {
        deckName: settings.Defaults.Deck,
        modelName: "",
        fields: {},
        options: {
            allowDuplicate: false,
            duplicateScope: "deck"
        },
        tags: [settings.Defaults.Tag]
    }
    result.EXISTING_IDS = await AnkiConnect.invoke('findNotes', {query: ""}) as number[]

    //RegExp section
    result.FROZEN_REGEXP = new RegExp(escapeRegex(settings.Syntax["Frozen Fields Line"]) + String.raw` - (.*?):\n((?:[^\n][\n]?)+)`, "g")
    result.DECK_REGEXP = new RegExp(String.raw`^` + escapeRegex(settings.Syntax["Target Deck Line"]) + String.raw`(?:\n|: )(.*)`, "m")
    result.TAG_REGEXP = new RegExp(String.raw`^` + escapeRegex(settings.Syntax["File Tags Line"]) + String.raw`(?:\n|: )(.*)`, "m")
    result.NOTE_REGEXP = new RegExp(String.raw`^` + escapeRegex(settings.Syntax["Begin Note"]) + String.raw`\n([\s\S]*?\n)` + escapeRegex(settings.Syntax["End Note"]), "gm")
    result.INLINE_REGEXP = new RegExp(escapeRegex(settings.Syntax["Begin Inline Note"]) + String.raw`(.*?)` + escapeRegex(settings.Syntax["End Inline Note"]), "g")
    result.EMPTY_REGEXP = new RegExp(escapeRegex(settings.Syntax["Delete Note Line"]) + ID_REGEXP_STR, "g")

    //Just a simple transfer
    result.curly_cloze = settings.Defaults.CurlyCloze
    result.highlights_to_cloze = settings.Defaults["CurlyCloze - Highlights to Clozes"]
    result.add_file_link = settings.Defaults["Add File Link"]
    result.comment = settings.Defaults["ID Comments"]
    result.add_context = settings.Defaults["Add Context"]
    result.add_obs_tags = settings.Defaults["Add Obsidian Tags"]

    return result
}
