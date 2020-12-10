export interface AnkiConnectNote {
	deckName: string,
	modelName: string,
	fields: Record<string, string>,
	options: {
		allowDuplicate: boolean,
		duplicateScope: string
	}
	tags: Array<string>,
}

export interface AnkiConnectNoteAndID {
	note: AnkiConnectNote,
	identifier: number | null
}
