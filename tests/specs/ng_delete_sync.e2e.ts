
import { readFileSync } from 'fs';
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

async function syncObsidianAnki() {
    const SyncButton = await $('aria/Obsidian_to_Anki - Scan Vault')
    await expect(SyncButton).toExist()
    await $(SyncButton).click()

    let logs: Array<Object> = [];
    do
    {
        logs = logs.concat( await browser.getLogs('browser'));
        console.log(logs);
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

    // await delay(500);
    // console.log(logs);
}

describe(test_name_fmt, () => {
    // before(async () => {
    //     // Clean Worker's Anki and Obs
    //     // ReInit Worker Anki and Obs
    //     // Worker WIll Auto Start ANki and Obs after 10Secs
        
    //     // cp -Rf tests/defaults/test_vault tests/ 
    //     // cp -Rf tests/defaults/test_config tests/

    //     try {
    //         fse.removeSync('tests/test_vault');
    //         if (fse.pathExistsSync('tests/test_vault'))
    //             console.log('The path still exists. Remove Failed');
    //         else
    //             console.log('Remove Success.')

    //         fse.copySync(`tests/defaults/test_vault`, `tests/test_vault`, { overwrite: true });
    //         if (fse.pathExistsSync('tests/test_vault'))
    //             console.log('Copied default Test_vault.');
    //         else
    //             console.log('Could not copy default Test_vault.')
    //         console.log('success copying default vault !');

    //         fse.copySync(`tests/defaults/test_vault_suites/${test_name}`, `tests/test_vault/${test_name}`, { overwrite: true });
    //         if (fse.pathExistsSync(`tests/test_vault/${test_name}`))
    //             console.log('Copied default Test_vault_suite.');
    //         else
    //             console.log('Could not copy default Test_vault_suite.')
    //     } catch (err) {
    //         console.error(err)
    //     }


    // })

    it('should send All-done message to console post sync', async () => {
        try {
            // fse.removeSync('tests/test_vault');
            // Wait for previous run Obsidian's test files to be saved properly
            while (fse.pathExistsSync('tests/test_vault/unlock'))
            {
                console.log('tests/test_vault still exists. Waiting for it be removed ...');
                await delay(100);
            }

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
          

            // fse.copySync(`tests/defaults/test_vault_suites/${test_name}`, `tests/test_vault/${test_name}`, { overwrite: true });
            // if (fse.pathExistsSync(`tests/test_vault/${test_name}`))
            //     console.log('Copied default Test_vault_suite.');
            // else
            //     console.log('Could not copy default Test_vault_suite.')
            
            // fse.removeSync('tests/config/.local/share/Anki2');
            // fse.copySync('tests/defaults/test_config/.local/share/Anki2', `tests/config/.local/share/Anki2`, { overwrite: true });

            fse.writeFile('tests/test_config/reset_perms', 'meow', (err) => {
                if (err)
                    console.log('reset_perms file could not be created. Err: ', err);
            });


        } catch (err) {
            console.error(err)
        }
        // ${test_name}
        // try {
        //     fse.copySync(`tests/defaults/test_vault_suites/${test_name}`, `tests/test_vault/${test_name}`, { overwrite: true });
        //     console.log('success copying vault !');
        // } catch (err) {
        //     console.error(err)
        // }

        await delay(5000);
        // await browser.debug();
        await browser.execute( () => { var btn = [...document.querySelectorAll('button')].find(btn => btn.textContent.includes('Trust')); if(btn) btn.click(); } );
        
        await delay(5000);
        await browser.execute( () => { return dispatchEvent(new KeyboardEvent('keydown', {'key': 'Escape'})); } );
        
        let folder = await $('.nav-folder-title*=ng_delete_sync')
        await expect(folder).toExist();
        await folder.click(); // Should drop down files

        let file = await $('.nav-file-title*=ng_delete_sync')
        await expect(folder).toExist();
        await file.click(); // Should open file in Editor

        await delay(100);        
        
        await browser.saveScreenshot(`logs/${test_name}/Obsidian PreTest.png`)
        // const SyncButton = await $('aria/Obsidian_to_Anki - Scan Vault')
        // await expect(SyncButton).toExist()
        // await $(SyncButton).click()

        // let logs: Array<Object> = [];
        // do
        // {
        //     logs = logs.concat( await browser.getLogs('browser'));
        //     console.log(logs);
        //     await delay(100);
        // }
        // while (!logs.find( e => (e['message'] as string).includes('All done!') ));

        // let warningsLogs = logs.filter( e => { return e['level'] == 'WARNING' });
        // let errorLogs = logs.filter( e => { return e['level'] == 'ERROR' || e['level'] == 'SEVERE' });

        // if (warningsLogs.length > 0 ) 
        // {
        //     console.warn(`${FgYellow}Warnings: `)
        //     console.warn(warningsLogs);
        //     console.warn(Reset)
        // }
        // if (errorLogs.length > 0 ) 
        // {
        //     console.error(`${FgRed}Errors: `);
        //     console.error(errorLogs);
        //     console.error(Reset)
        // }

        // // await delay(500);
        // console.log(logs);
        // console.log('Synced Obsidian and Anki ... Existing Obisdian');
        await syncObsidianAnki();        
        await browser.saveScreenshot(`logs/${test_name}/Obsidian PostTest.png`)
        
        // await browser.debug(); // You can safely Pause for debugging here, else it may create unintended consequences
        // await browser.execute( () => { return window.open('','_self').close(); } );
        await delay(1000); // esp for PostTest ss of Anki and wait for obsidian teardown               
    })

    it('should have Anki card IDs in Obsidian note', async () => {
        // const fileDefault = readFileSync( path.join(__dirname,`./../../tests/defaults/test_vault_suites/${test_name}/${test_name}.md`), 'utf-8');
        const filePostTest = readFileSync( path.join(__dirname,`./../../tests/test_vault/${test_name}/${test_name}.md`), 'utf-8');
        
        const ID_REGEXP_STR = /\n?(?:<!--)?(?:ID: (\d+).*?)/g;
        const ID_REGEXP_STR_CARD = /<!-- CARD -->/g;

        let number_of_cards = (filePostTest.match(ID_REGEXP_STR) || []).length;
        let number_of_test_cards = (filePostTest.match(ID_REGEXP_STR_CARD) || []).length;

        console.log(`Number of cards in test file are - ${number_of_cards}, number_of_test_cards - ${number_of_test_cards}`);
        
        assert (number_of_cards == number_of_test_cards);
        // assert( fileDefault.split('\n').length == filePostTest.split('\n').length-number_of_cards ) 
        // fse.writeFile('tests/test_vault/unlock', 'meow', (err) => {
        //     if (err)
        //         console.log('reset_perms file could not be created. Err: ', err);
        // });

        // await delay(5000); // >3000ms req; the last test of this spec, wait for anki and obsidian to close properly
    })

    it('post delete, it should not give any errors', async () => {
        await browser.execute( () => { 
            var span = [...document.querySelectorAll('span')].find(s => s.textContent.includes('REPLACE ME FOR TEST')); 
            if(span)
            {
                span.innerText = 'DELETE'                
            }
        });

        const newline = await $('div*=DELETE')
        await expect(newline).toExist()
        
        await browser.execute( () => { return dispatchEvent(new KeyboardEvent('keydown', {'key': 's', ctrlKey: true})); } );

        await syncObsidianAnki();        
        await browser.saveScreenshot(`logs/${test_name}/Obsidian PostTest2.png`)

        // await browser.debug();
        await browser.closeWindow();
        
        await delay(3000); // esp for PostTest ss of Anki and wait for obsidian teardown

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

    it('should have not have Anki ID in note', async () => {
        const fileDefault = readFileSync( path.join(__dirname,`./../../tests/defaults/test_vault_suites/${test_name}/${test_name}.md`), 'utf-8');
        const filePostTest = readFileSync( path.join(__dirname,`./../../tests/test_vault/${test_name}/${test_name}.md`), 'utf-8');
        
        const ID_REGEXP_STR = /\n?(?:<!--)?(?:ID: (\d+).*?)/g;
        const ID_REGEXP_STR_CARD = /<!-- CARD -->/g;

        let number_of_cards = (filePostTest.match(ID_REGEXP_STR) || []).length;
        let number_of_test_cards = (filePostTest.match(ID_REGEXP_STR_CARD) || []).length;

        console.log(`Number of cards in test file are - ${number_of_cards}, number_of_test_cards - ${number_of_test_cards}`);
        
        expect(number_of_cards).toBe(0)
        expect(number_of_test_cards).toBe(1)

        fse.writeFile('tests/test_vault/unlock', 'meow', (err) => {
            if (err)
                console.log('reset_perms file could not be created. Err: ', err);
        });

        await delay(5000); // >3000ms req; the last test of this spec, wait for anki and obsidian to close properly
    })
})

