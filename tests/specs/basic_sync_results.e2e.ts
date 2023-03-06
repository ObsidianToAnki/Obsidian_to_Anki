
import { readFileSync } from 'fs';
const path = require('path');
const assert = require('assert');

describe('Basic Sync result', () => {
    it('should have Anki card IDs in Obsidian note', async () => {
        const fileDefault = readFileSync( path.join(__dirname,'./../../tests/defaults/test_vault/Test.md'), 'utf-8');
        const filePostTest = readFileSync( path.join(__dirname,'./../../tests/test_vault/Test.md'), 'utf-8');

        assert( fileDefault.split('\n').length == filePostTest.split('\n').length-2 ) 
    })
})
