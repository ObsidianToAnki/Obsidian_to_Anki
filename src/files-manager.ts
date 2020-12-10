/*Class for managing a list of files, and their Anki requests.*/
import { ExternalAppData } from './interfaces/settings-interface'
import { App, TFile } from 'obsidian'
import { RegexFile, File} from './file'
import * as AnkiConnect from './anki'

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
                    this.data,
                    this.data.custom_regexps
                )
            )
        }
    }

    async genFiles() {
        for (let file of this.files) {
            const content: string = await this.app.vault.read(file)
            this.ownFiles.push(
                new File(
                    await this.app.vault.read(file),
                    file.path,
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
        console.log("Requesting update of fields of existing notes")
        for (let file of this.ownFiles) {
            temp.push(file.getUpdateFields())
        }
        requests.push(AnkiConnect.multi(temp))
        temp = []
        console.log("Requesting card IDs of notes to be edited...")
        for (let file of this.ownFiles) {
            temp.push(file.getNoteInfo())
        }
        requests.push(AnkiConnect.multi(temp))
        temp = []
        console.log("Requesting deletion of notes..")
        for (let file of this.ownFiles) {
            temp.push(file.getDeleteNotes())
        }
        requests.push(AnkiConnect.multi(temp))
        this.requests_1_result = AnkiConnect.invoke('multi', {actions: requests})
        console.log(this.requests_1_result)
    }

}
