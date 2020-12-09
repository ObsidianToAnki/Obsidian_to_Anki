interface NOTE_OPTIONS {
	allowDuplicate: boolean,
	duplicateScope: string,
}

export interface NOTE {
	deckName: string,
	modelName: string,
	fields: Record<string, string>,
	options: NOTE_OPTIONS,
	tags: Array<string>,
	audio: Array<any>
}

export interface NOTE_AND_ID {
	note: NOTE,
	identifier: number
}
