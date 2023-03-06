
function delay(ms: number) {
    return new Promise( resolve => setTimeout(resolve, ms) );
}

describe('Basic Sync', () => {
    it('should send All-done message to console post sync', async () => {

        await delay(5000)
        await browser.execute( () => { return [...document.querySelectorAll('button')].find(btn => btn.textContent.includes('Trust')).click(); } );
        
        await delay(5000)
        await browser.execute( () => { return dispatchEvent(new KeyboardEvent('keydown', {'key': 'Escape'})); } );
        
        await delay(100)        
        
        await browser.saveScreenshot('logs/Obsidian PreTest.png')
        const SyncButton = await $('aria/Obsidian_to_Anki - Scan Vault')
        await expect(SyncButton).toExist()
        await $(SyncButton).click()

        let logs: Array<Object>;
        do
        {
            logs = await browser.getLogs('browser');
            await delay(100);
        }
        while (!logs.find( e => (e['message'] as string).includes('All done!') ));

        await delay(500);
        console.log(logs);
        console.log('Synced Obsidian and Anki ... Existing Obisdian');
        await browser.saveScreenshot('logs/Obsidian PostTest.png')
        
        await browser.execute( () => { return window.open('','_self').close(); } );
        await delay(5000); // esp for PostTest ss of Anki
        // await browser.debug()
    })
})

