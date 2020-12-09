export interface PluginSettings {
	CUSTOM_REGEXPS: Record<string, string>,
	Syntax: {
		"Begin Note": string,
		"End Note": string,
		"Begin Inline Note": string,
		"End Inline Note": string,
		"Target Deck Line": string,
		"File Tags Line": string,
		"Delete Regex Note Line": string,
		"Frozen Fields Line": string
	},
	Defaults: {
		"Add File Link": boolean,
		"Tag": string,
		"Deck": string,
		"CurlyCloze": boolean,
		"Regex": boolean,
		"ID Comments": boolean,
	}
}
