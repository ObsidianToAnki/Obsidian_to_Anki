/*Class for managing a list of files, and their Anki requests.*/
import { ExternalAppData } from './interfaces/settings-interface'
import { App, TFile } from 'obsidian'
import { RegexFile, File} from './file'
import * as AnkiConnect from './anki'

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
    3: any

}


export class FileManager {
    app: App
    data: ExternalAppData
    files: TFile[]
    ownFiles: Array<File | RegexFile>
    file_hashes: Record<string, string>
    requests_1_result: any

    constructor(app: App, data:ExternalAppData, files: TFile[], file_hashes: Record<string, string>) {
        this.app = app
        this.data = data
        this.files = files
        this.ownFiles = []
        this.file_hashes = file_hashes
    }

    getUrl(file: TFile): string {
        return "obsidian://open?vault=" + encodeURIComponent(this.data.vault_name) + "&file=" + encodeURIComponent(file.path)
    }

    async initialiseFiles() {
        if (this.data.regex) {
            await this.genRegexFiles()
        } else {
            await this.genFiles()
        }
        let files_changed: Array<File | RegexFile> = []
        for (let file of this.ownFiles) {
            if (this.file_hashes.hasOwnProperty(file.path) && file.getHash() === this.file_hashes[file.path]) {
                //Indicates we've seen it in a scan before
                console.log("Skipping ", file.path, "as we've scanned it before.")
            } else {
                file.scanFile()
                files_changed.push(file)
            }
        }
        this.ownFiles = files_changed
    }

    async genRegexFiles() {
        for (let file of this.files) {
            const content: string = await this.app.vault.read(file)
            this.ownFiles.push(
                new RegexFile(
                    content,
                    file.path,
                    this.data.add_file_link ? this.getUrl(file) : "",
                    this.data,
                )
            )
        }
    }

    async genFiles() {
        for (let file of this.files) {
            const content: string = await this.app.vault.read(file)
            this.ownFiles.push(
                new File(
                    content,
                    file.path,
                    this.data.add_file_link ? this.getUrl(file) : "",
                    this.data
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
        this.requests_1_result = await AnkiConnect.invoke('multi', {actions: requests})
        this.parse_requests_1()
    }

    async parse_requests_1() {
        const response = this.requests_1_result as Requests1Result
        const note_ids_array_by_file = AnkiConnect.parse(response[0])
        const note_info_array_by_file = AnkiConnect.parse(response[1])
        const tag_list: string[] = AnkiConnect.parse(response[2])
        for (let index in note_ids_array_by_file) {
            let i: number = parseInt(index)
            let file = this.ownFiles[i]
            const file_response = note_ids_array_by_file[i]
            file.note_ids = []
            for (let response of AnkiConnect.parse(file_response)) {
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
    }



}
