/*Class for managing a list of files, and their Anki requests.*/
import { ParsedSettings } from './interfaces/settings-interface'
import { App, TFile, CachedMetadata } from 'obsidian'
import { AllFile } from './file'
import * as AnkiConnect from './anki'
import { bytesToBase64 } from 'byte-base64'
import { basename } from 'path'

interface addNoteResponse {
    result: number,
    error: string | null
}

interface notesInfoResponse {
    result: Array<{
        noteId: number,
        modelName: string,
        tags: string[],
        fields: Record<string, {
            order: number,
            value: string
        }>,
        cards: number[]
    }>,
    error: string | null
}

interface Requests1Result {
    0: {
        error: string | null,
        result: Array<{
            result: addNoteResponse[],
            error: string | null
        }>
    },
    1: {
        error: string | null,
        result: notesInfoResponse[]
    },
    2: any,
    3: any,
    4: any

}

function difference<T>(setA: Set<T>, setB: Set<T>): Set<T> {
    let _difference = new Set(setA)
    for (let elem of setB) {
        _difference.delete(elem)
    }
    return _difference
}


export class FileManager {
    app: App
    data: ParsedSettings
    files: TFile[]
    ownFiles: Array<AllFile>
    file_hashes: Record<string, string>
    requests_1_result: any
    added_media_set: Set<string>

    constructor(app: App, data:ParsedSettings, files: TFile[], file_hashes: Record<string, string>, added_media: string[]) {
        this.app = app
        this.data = data
        this.files = files
        this.ownFiles = []
        this.file_hashes = file_hashes
        this.added_media_set = new Set(added_media)
    }

    getUrl(file: TFile): string {
        return "obsidian://open?vault=" + encodeURIComponent(this.data.vault_name) + String.raw`&file=` + encodeURIComponent(file.path)
    }

    async initialiseFiles() {
        await this.genAllFiles()
        let files_changed: Array<AllFile> = []
        let obfiles_changed: TFile[] = []
        for (let index in this.ownFiles) {
            const i = parseInt(index)
            let file = this.ownFiles[i]
            if (this.file_hashes.hasOwnProperty(file.path) && file.getHash() === this.file_hashes[file.path]) {
                //Indicates we've seen it in a scan before
                console.log("Skipping ", file.path, "as we've scanned it before.")
            } else {
                file.scanFile()
                files_changed.push(file)
                obfiles_changed.push(this.files[i])
            }
        }
        this.ownFiles = files_changed
        this.files = obfiles_changed
    }

    async genAllFiles() {
        for (let file of this.files) {
            const content: string = await this.app.vault.read(file)
            const cache: CachedMetadata = this.app.metadataCache.getCache(file.path)
            this.ownFiles.push(
                new AllFile(
                    content,
                    file.path,
                    this.data.add_file_link ? this.getUrl(file) : "",
                    this.data,
                    cache
                )
            )
        }
    }

    async requests_1() {
        let requests: AnkiConnect.AnkiConnectRequest[] = []
        let temp: AnkiConnect.AnkiConnectRequest[] = []
        console.log("Requesting addition of notes into Anki...")
        for (let file of this.ownFiles) {
            temp.push(file.getAddNotes())
        }
        requests.push(AnkiConnect.multi(temp))
        temp = []
        console.log("Requesting card IDs of notes to be edited...")
        for (let file of this.ownFiles) {
            temp.push(file.getNoteInfo())
        }
        requests.push(AnkiConnect.multi(temp))
        temp = []
        console.log("Requesting tag list...")
        requests.push(AnkiConnect.getTags())
        console.log("Requesting update of fields of existing notes")
        for (let file of this.ownFiles) {
            temp.push(file.getUpdateFields())
        }
        requests.push(AnkiConnect.multi(temp))
        temp = []
        console.log("Requesting deletion of notes..")
        for (let file of this.ownFiles) {
            temp.push(file.getDeleteNotes())
        }
        requests.push(AnkiConnect.multi(temp))
        temp = []
        console.log("Requesting addition of media...")
        for (let file of this.ownFiles) {
            const mediaLinks = difference(file.formatter.detectedMedia, this.added_media_set)
            for (let mediaLink of mediaLinks) {
                console.log("Adding media file: ", mediaLink)
                this.added_media_set.add(mediaLink)
                const dataFile = this.app.metadataCache.getFirstLinkpathDest(mediaLink, file.path)
                const data = await this.app.vault.readBinary(dataFile)
                temp.push(
                    AnkiConnect.storeMediaFile(
                        basename(mediaLink),
                        bytesToBase64(
                            new Uint8Array(data)
                        )
                    )
                )
            }
        }
        requests.push(AnkiConnect.multi(temp))
        temp = []
        this.requests_1_result = await AnkiConnect.invoke('multi', {actions: requests})
        await this.parse_requests_1()
    }

    async parse_requests_1() {
        const response = this.requests_1_result as Requests1Result
        let note_ids_array_by_file: Requests1Result[0]["result"]
        try {
            note_ids_array_by_file = AnkiConnect.parse(response[0])
        } catch(error) {
            console.log("Error: ", error)
            note_ids_array_by_file = response[0].result
        }
        const note_info_array_by_file = AnkiConnect.parse(response[1])
        const tag_list: string[] = AnkiConnect.parse(response[2])
        for (let index in note_ids_array_by_file) {
            let i: number = parseInt(index)
            let file = this.ownFiles[i]
            let file_response: addNoteResponse[]
            try {
                file_response = AnkiConnect.parse(note_ids_array_by_file[i])
            } catch(error) {
                console.log("Error: ", error)
                file_response = note_ids_array_by_file[i].result
            }
            file.note_ids = []
            for (let response of file_response) {
                file.note_ids.push(AnkiConnect.parse(response))
            }
        }
        for (let index in note_info_array_by_file) {
            let i: number = parseInt(index)
            let file = this.ownFiles[i]
            const file_response = AnkiConnect.parse(note_info_array_by_file[i])
            let temp: number[] = []
            for (let note_response of file_response) {
                temp.push(...note_response.cards)
            }
            file.card_ids = temp
        }
        for (let index in this.ownFiles) {
            let i: number = parseInt(index)
            let ownFile = this.ownFiles[i]
            let obFile = this.files[i]
            ownFile.tags = tag_list
            ownFile.writeIDs()
            ownFile.removeEmpties()
            if (ownFile.file !== ownFile.original_file) {
                await this.app.vault.modify(obFile, ownFile.file)
            }
        }
        await this.requests_2()
    }

    getHashes(): Record<string, string> {
        let result: Record<string, string> = {}
        for (let file of this.ownFiles) {
            result[file.path] = file.getHash()
        }
        return result
    }

    async requests_2(): Promise<void> {
        let requests: AnkiConnect.AnkiConnectRequest[] = []
        let temp: AnkiConnect.AnkiConnectRequest[] = []
        console.log("Requesting cards to be moved to target deck...")
        for (let file of this.ownFiles) {
            temp.push(file.getChangeDecks())
        }
        requests.push(AnkiConnect.multi(temp))
        temp = []
        console.log("Requesting tags to be replaced...")
        for (let file of this.ownFiles) {
            temp.push(file.getClearTags())
        }
        requests.push(AnkiConnect.multi(temp))
        temp = []
        for (let file of this.ownFiles) {
            temp.push(file.getAddTags())
        }
        requests.push(AnkiConnect.multi(temp))
        temp = []
        await AnkiConnect.invoke('multi', {actions: requests})
        console.log("All done!")
    }



}
