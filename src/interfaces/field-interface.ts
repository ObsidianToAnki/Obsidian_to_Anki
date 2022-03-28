export type FIELDS_DICT = Record<string, string[]>
/*
The keys are note type names.
The values are a list of fields for this note type,
given by the `modelFieldNames` method from AnkiConnect.
The list of fields is in order.

Example instance:

const example_fields_dict : FIELDS_DICT = {
    "Basic": ["Front", "Back"],
    "Cloze": ["Text, Extra"]
}
*/

export type FROZEN_FIELDS_DICT = Record<string, Record<string, string>>
/*
The keys are note type names.
Given a particular note type, the value associated is a dictionary,
where the keys are field names, and the values are the "frozen" parts of
the field names, meant to be appended to the field when parsing the file.

Example instance:

const example_frozen_dict: FROZEN_FIELDS_DICT = {
    "Basic": {"Front": "Hello", "Back": "World!"},
    "Cloze": {"Text": "Geography"}
}
*/
