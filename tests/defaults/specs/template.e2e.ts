

import { glob } from "glob";
import { browser } from '@wdio/globals';

const fse = require('fs-extra');
const path = require('path');
const assert = require('assert');

const test_name = (path.basename(__filename) as string).split('.')[0] 
const test_name_fmt = test_name.split('_').reduce((acc,s) => { return acc + ' ' + s.charAt(0).toUpperCase() + s.slice(1)}) + " Test"

const FgYellow = "\x1b[33m"
const Reset = "\x1b[0m"
const FgRed = "\x1b[31m"

function delay(ms: number) {
    return new Promise( resolve => setTimeout(resolve, ms) );
}

describe(test_name_fmt, () => {

    it('should send All-done message to console post sync', async () => {
        try {
            // fse.removeSync('tests/test_vault');
            // Wait for previous run Obsidian's test files to be saved properly
            while (fse.pathExistsSync('tests/test_vault/unlock'))
            {
                console.log('tests/test_vault still exists. Waiting for it be removed ...');
                await delay(100);
            }
            await delay(5000);

            fse.copySync(`tests/defaults/test_vault`, `tests/test_vault`, { overwrite: true });
            if (fse.pathExistsSync('tests/test_vault'))
                console.log('Copied default Test_vault.');
            else
                console.log('Could not copy default Test_vault.')
            console.log('success copying default vault !');

            fse.copySync(`tests/defaults/test_vault_suites/${test_name}`, `tests/test_vault/${test_name}`, { overwrite: true });
            if (fse.pathExistsSync(`tests/test_vault/${test_name}`))
                console.log('Copied default Test_vault_suite.');
            else
                console.log('Could not copy default Test_vault_suite.')

            if (fse.pathExistsSync(`tests/defaults/test_vault_suites/${test_name}/.obsidian`))
                fse.copySync(`tests/defaults/test_vault_suites/${test_name}/.obsidian`, `tests/test_vault/.obsidian`, { overwrite: true });
          
            fse.writeFile('tests/test_config/reset_perms', 'meow', (err) => {
                if (err)
                    console.log('reset_perms file could not be created. Err: ', err);
            });
        } catch (err) {
            console.error(err)
        }

        // const TrustButton = await $('button*=Trust')
        // await expect(TrustButton).toExist()
        await delay(2000); // even for reset perms
        await browser.execute( () => { var btn = [...document.querySelectorAll('button')].find(btn => btn.textContent.includes('Trust')); if(btn) btn.click(); } );
        
        await delay(3000);
        await browser.execute( () => { return dispatchEvent(new KeyboardEvent('keydown', {'key': 'Escape'})); } );
        // await browser.execute( () => { return dispatchEvent(new KeyboardEvent('keydown', {'key': 'r', ctrlKey: true, shiftKey: true})); } );        
        // await delay(100);
        
        let SyncButton = await $('aria/Obsidian_to_Anki - Scan Vault')
        await expect(SyncButton).toExist()
        await browser.execute( () => { return dispatchEvent(new KeyboardEvent('keydown', {'key': 'r', ctrlKey: true, shiftKey: true})); } );        
        await delay(2000);

        let folder = await $(`.nav-folder-title*=${test_name}`)
        await expect(folder).toExist();
        await folder.click(); // Should drop down files

        let file = await $(`.nav-file-title*=${test_name}`)
        await expect(file).toExist();
        await file.click(); // Should open file in Editor

        SyncButton = await $('aria/Obsidian_to_Anki - Scan Vault')
        await expect(SyncButton).toExist()

        await browser.saveScreenshot(`logs/${test_name}/Obsidian PreTest.png`)
        await $(SyncButton).click()

        let logs: Array<Object> = [];
        do
        {
            logs = logs.concat( await browser.getLogs('browser'));
            console.log(logs);

            if (logs.find( e => (e['level'] as string).includes('SEVERE') ))
                break;

            await delay(100);
        }
        while (!logs.find( e => (e['message'] as string).includes('All done!') ));

        let warningsLogs = logs.filter( e => { return e['level'] == 'WARNING' });
        let errorLogs = logs.filter( e => { return e['level'] == 'ERROR' || e['level'] == 'SEVERE' });

        if (warningsLogs.length > 0 ) 
        {
            console.warn(`${FgYellow}Warnings: `)
            console.warn(warningsLogs);
            console.warn(Reset)
        }
        if (errorLogs.length > 0 ) 
        {
            console.error(`${FgRed}Errors: `);
            console.error(errorLogs);
            console.error(Reset)
        }

        await browser.saveScreenshot(`logs/${test_name}/Obsidian PostTest.png`)

        if( errorLogs.length > 0 || warningsLogs.length > 0)
        {            
            await browser.execute( () => { return dispatchEvent(new KeyboardEvent('keydown', {'key': 'i', ctrlKey: true, shiftKey: true})); } );   
            await delay(1000);
            await browser.saveScreenshot(`logs/${test_name}/Obsidian PostTest_Error.png`)
        }
        await delay(1000);

        console.log(logs);
        console.log('Synced Obsidian and Anki ... Existing Obisdian');        
        // await browser.debug(); // You can safely Pause for debugging here, else it may create unintended consequences
        await browser.closeWindow();
        await delay(1000); // esp for PostTest ss of Anki and wait for obsidian teardown
        
        try {
            function errHandler(err) {
                if (err) {
                    console.log(`Error on trying to copy vault_suite ${test_name}:`, err);
                }
            }

            fse.copyFile(`tests/test_config/Anki PreTest_${test_name}.png`, `logs/${test_name}/Anki PreTest_${test_name}.png`, errHandler);
            fse.copyFile(`tests/test_config/Anki PostTest_${test_name}.png`, `logs/${test_name}/Anki PostTest_${test_name}.png`, errHandler);
        }
        catch( e ) {
            console.error( "We've thrown! Whoops!", e );
        }
              
    })

    it('should have Anki card IDs in Obsidian note', async () => {
        const test_vault = path.join(__dirname,`./../test_vault/${test_name}/**/*.md`) //${test_name}

        const ID_REGEXP_STR = /\n?(?:<!--)?(?:ID: (\d+).*?)/g;
        const ID_REGEXP_STR_CARD = /<!-- CARD -->/g;

        const files = await glob('tests/test_vault/**/*.md')

        for (const file of files)
        {
            const filePostTest = fse.readFileSync(file, 'utf-8');
            
            let number_of_cards = (filePostTest.match(ID_REGEXP_STR) || []).length;
            let number_of_test_cards = (filePostTest.match(ID_REGEXP_STR_CARD) || []).length;

            console.log(`Number of cards in test file ${file} are - ${number_of_cards}, number_of_test_cards - ${number_of_test_cards}`);
            
            assert (number_of_cards == number_of_test_cards);
        }

        fse.writeFile('tests/test_vault/unlock', 'meow', (err) => {
            if (err)
                console.log('unlock file could not be created. Err: ', err);
        });
        await delay(5000); // >3000ms req; the last test of this spec, wait for anki and obsidian to close properly
    })
})

