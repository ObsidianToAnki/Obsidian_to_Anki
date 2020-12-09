/*Manages parsing notes into a dictionary formatted for AnkiConnect.

Input must be the note text.
Does NOT deal with finding the note in the file.*/


export class Note {

    text: string
    split_text: string[]
    current_field_num: number
    delete: boolean
    identifier: number
    tags: string[]
    note_type: string
    field_names: string[]
    current_field: string
    FIELDS_DICT: Record<string, string>
    ID_REGEXP: RegExp = /(?:<!--)?ID: (\d+)/

    constructor(note_text: string, FIELDS_DICT: Record<string, string>) {
        this.text = note_text.trim()
        this.current_field_num = 0
        this.delete = false
        this.split_text = this.getSplitText()
        this.identifier = this.getIdentifier()
        if (!this.split_text) {
            //This indicates a delete action. So!
            this.delete = true
            return
        }


    }

    getSplitText(): string[] {
        return this.text.split("\n")
    }

    getIdentifier(): number | null {
        if (this.ID_REGEXP.test(this.split_text[-1])) {
            return parseInt(this.ID_REGEXP.exec(this.split_text.pop())[1])
        } else {
            return null
        }
    }

}
