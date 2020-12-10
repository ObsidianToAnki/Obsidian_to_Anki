const ANKI_PORT: number = 8765

import { AnkiConnectNote } from './interfaces/note-interface'

export interface AnkiConnectRequest {
	action: string,
	version: 6,
	params: any
}

export function invoke(action: string, params={}) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest()
        xhr.addEventListener('error', () => reject('failed to issue request'));
        xhr.addEventListener('load', () => {
            try {
                const response = JSON.parse(xhr.responseText);
                if (Object.getOwnPropertyNames(response).length != 2) {
                    throw 'response has an unexpected number of fields';
                }
                if (!response.hasOwnProperty('error')) {
                    throw 'response is missing required error field';
                }
                if (!response.hasOwnProperty('result')) {
                    throw 'response is missing required result field';
                }
                if (response.error) {
                    throw response.error;
                }
                resolve(response.result);
            } catch (e) {
                reject(e);
            }
        });

        xhr.open('POST', 'http://127.0.0.1:' + ANKI_PORT.toString());
        xhr.send(JSON.stringify({action, version: 6, params}));
    });
}

export function parse<T>(response: {error: string, result: T}): T {
	//Helper function for parsing the result of a multi
	if (Object.getOwnPropertyNames(response).length != 2) {
		throw 'response has an unexpected number of fields'
	}
	if (!(response.hasOwnProperty('error'))) {
		throw 'response is missing required error field'
	}
	if (!(response.hasOwnProperty('result'))) {
		throw 'response is missing required result field';
	}
	if (response.error) {
		throw response.error
	}
	return response.result
}

// All the rest of these functions only return request objects as opposed to actually carrying out the action. For efficiency!

function request(action: string, params={}): AnkiConnectRequest {
	return {action, version:6, params}
}

export function multi(actions: AnkiConnectRequest[]): AnkiConnectRequest {
	return request('multi', {actions: actions})
}

export function addNote(note: AnkiConnectNote): AnkiConnectRequest {
	return request('addNote', {note: note})
}

export function deleteNotes(note_ids: number[]): AnkiConnectRequest {
	return request('deleteNotes', {notes: note_ids})
}

export function updateNoteFields(id: number, fields: Record<string, string>): AnkiConnectRequest {
	return request(
		'updateNoteFields', {
			note: {
				id: id,
				fields: fields
			}
		}
	)
}

export function notesInfo(note_ids: number[]): AnkiConnectRequest {
	return request(
		'notesInfo', {
			notes: note_ids
		}
	)
}

export function changeDeck(card_ids: number[], deck: string): AnkiConnectRequest {
	return request(
		'changeDeck', {
			cards: card_ids,
			deck: deck
		}
	)
}

export function removeTags(note_ids: number[], tags: string): AnkiConnectRequest {
	return request(
		'removeTags', {
			notes: note_ids,
			tags: tags
		}
	)
}

export function addTags(note_ids: number[], tags: string): AnkiConnectRequest {
	return request(
		'addTags', {
			notes: note_ids,
			tags: tags
		}
	)
}

export function getTags(): AnkiConnectRequest {
	return request('getTags')
}
