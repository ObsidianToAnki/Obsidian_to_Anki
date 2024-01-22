import type { Options } from '@wdio/types'
const fs = require('fs')
const fse = require('fs-extra');
const path = require('path');

export const config/* : Options.Testrunner */ = {
    //
    // ====================
    // Runner Configuration
    // ====================
    // WebdriverIO supports running e2e tests as well as unit and component tests.
    runner: 'local',
    autoCompileOpts: {
        tsNodeOpts: {
            project: './tests/tsconfig.json'
        }
    },
        
    //
    // ==================
    // Specify Test Files
    // ==================
    // Define which test specs should run. The pattern is relative to the directory
    // of the configuration file being run.
    //
    // The specs are defined as an array of spec files (optionally using wildcards
    // that will be expanded). The test for each spec file will be run in a separate
    // worker process. In order to have a group of spec files run in the same worker
    // process simply enclose them in an array within the specs array.
    //
    // If you are calling `wdio` from an NPM script (see https://docs.npmjs.com/cli/run-script),
    // then the current working directory is where your `package.json` resides, so `wdio`
    // will be called from there.
    //
    specs: [
        // [
            // './tests/specs_gen/**/*.ts',
            './tests/specs_gen/**/*.ts',
            './tests/specs/**/*.ts'
        // ]
    ],
    // Patterns to exclude.
    exclude: [
        // 'path/to/excluded/files'
    ],
    //
    // ============
    // Capabilities
    // ============
    // Define your capabilities here. WebdriverIO can run multiple capabilities at the same
    // time. Depending on the number of capabilities, WebdriverIO launches several test
    // sessions. Within your capabilities you can overwrite the spec and exclude options in
    // order to group specific specs to a specific capability.
    //
    // First, you can define how many instances should be started at the same time. Let's
    // say you have 3 different capabilities (Chrome, Firefox, and Safari) and you have
    // set maxInstances to 1; wdio will spawn 3 processes. Therefore, if you have 10 spec
    // files and you set maxInstances to 10, all spec files will get tested at the same time
    // and 30 processes will get spawned. The property handles how many capabilities
    // from the same test should run tests.
    //
    maxInstances: 1,
    //
    // If you have trouble getting all important capabilities together, check out the
    // Sauce Labs platform configurator - a great tool to configure your capabilities:
    // https://saucelabs.com/platform/platform-configurator
    //
    capabilities: [{
    
        // maxInstances can get overwritten per capability. So if you have an in-house Selenium
        // grid with only 5 firefox instances available you can make sure that not more than
        // 5 instances get started at a time.
        // maxInstances: 5,
        //
        browserName: 'chrome',
        acceptInsecureCerts: true,
        // 'goog:chromeOptions': {
        //     args: [
        //         '--no-sandbox',
        //         '--disable-infobars',
        //         '--headless',
        //         '--disable-gpu',
        //         '--window-size=1440,735'
        //     ],
        // }
        'goog:chromeOptions': {
            // binary: '/squashfs-root/obsidian', // Path to your Electron binary
            args: [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--window-size=1440,735'
            ],
            debuggerAddress: '127.0.0.1:8888'
            // args: [/* cli arguments */] // Optional, perhaps 'app=' + /path/to/your/app/
        },
        "goog:loggingPrefs": {   // <-- Add this
          browser: "ALL",
        },
        // If outputDir is provided WebdriverIO can capture driver session logs
        // it is possible to configure which logTypes to include/exclude.
        // excludeDriverLogs: ['*'], // pass '*' to exclude all driver session logs
        // excludeDriverLogs: ['bugreport', 'server'],
    }],
    //
    // ===================
    // Test Configurations
    // ===================
    // Define all options that are relevant for the WebdriverIO instance here
    //
    // Level of logging verbosity: trace | debug | info | warn | error | silent
    logLevel: 'debug',
    //
    // Set specific log levels per logger
    // loggers:
    // - webdriver, webdriverio
    // - @wdio/browserstack-service, @wdio/devtools-service, @wdio/sauce-service
    // - @wdio/mocha-framework, @wdio/jasmine-framework
    // - @wdio/local-runner
    // - @wdio/sumologic-reporter
    // - @wdio/cli, @wdio/config, @wdio/utils
    // Level of logging verbosity: trace | debug | info | warn | error | silent
    // logLevels: {
    //     webdriver: 'info',
    //     '@wdio/appium-service': 'info'
    // },
    //
    // If you only want to run your tests until a specific amount of tests have failed use
    // bail (default is 0 - don't bail, run all tests).
    bail: 0,
    //
    // Set a base URL in order to shorten url command calls. If your `url` parameter starts
    // with `/`, the base url gets prepended, not including the path portion of your baseUrl.
    // If your `url` parameter starts without a scheme or `/` (like `some/path`), the base url
    // gets prepended directly.
    baseUrl: 'http://localhost', //:8080',    
    // path: '/wd/hub', // Required to work with wdio v6
    // port: 9515,
    //
    // Default timeout for all waitFor* commands.
    waitforTimeout: 10000,
    //
    // Default timeout in milliseconds for request
    // if browser driver or grid doesn't send response
    connectionRetryTimeout: 120000,
    //
    // Default request retries count
    connectionRetryCount: 3,
    //
    // Test runner services
    // Services take over a specific job you don't want to take care of. They enhance
    // your test setup with almost no effort. Unlike plugins, they don't add new
    // commands. Instead, they hook themselves up into the test process.
    // automationProtocol: 'devtools',
    services: [ 
        [ 'chromedriver', {
            logFileName: 'wdio-chromedriver.log', // default
            outputDir: 'logs', // overwrites the config.outputDir
            args: ['--silent']            
        }], 
        'docker'
    ],

    dockerLogs: 'logs',
    dockerOptions: {        
        image: 'anki-obsidian',
        healthCheck: 'http://localhost:8080',
        options: {
            p: ['8080:8080', '8888:8888'],
            // shmSize: '2g',
            d: true,
            // eg. cmd, docker run -e LANG=C.UTF-8 -e DISPLAY=$DISPLAY -e LC_ALL=C.UTF-8 -it -v D:\\\\Users\\Documents\\GitHub\\Obsidian_to_Anki\\tests\\test_vault:/vaults -v D:\\\\Users\\Documents\\GitHub\\Obsidian_to_Anki\\tests\\test_config:/config -p 8080:8080 debian-anki
            e: ['LANG=C.UTF-8', 'DISPLAY=$DISPLAY', 'LC_ALL=C.UTF-8'], 
            v: [
                `${ path.join(__dirname, '/tests/test_vault') }:/vaults`,
                `${ path.join(__dirname, '/tests/test_config') }:/config`
            ]
        }        
    },
    // Framework you want to run your specs with.
    // The following are supported: Mocha, Jasmine, and Cucumber
    // see also: https://webdriver.io/docs/frameworks
    //
    // Make sure you have the wdio adapter package for the specific framework installed
    // before running any tests.
    framework: 'mocha',
    //
    // The number of times to retry the entire specfile when it fails as a whole
    // specFileRetries: 1,
    //
    // Delay in seconds between the spec file retry attempts
    // specFileRetriesDelay: 10,
    //
    // Whether or not retried specfiles should be retried immediately or deferred to the end of the queue
    // specFileRetriesDeferred: false,
    //
    // Test reporter for stdout.
    // The only one supported by default is 'dot'
    // see also: https://webdriver.io/docs/dot-reporter
    reporters: [ 
        [ 'junit', {
            outputDir: 'logs/test-reports/',
            outputFileFormat: function(options) { // optional
                return `wdio.xml`
            },
            errorOptions: {
                error: 'message',
                failure: 'message',
                stacktrace: 'stack'
            }
        }]
    ],
    outputDir: 'logs',
    //
    // Options to be passed to Mocha.
    // See the full list at http://mochajs.org/
    mochaOpts: {
        ui: 'bdd',
        timeout: 60000
    },
    //
    // =====
    // Hooks
    // =====
    // WebdriverIO provides several hooks you can use to interfere with the test process in order to enhance
    // it and to build services around it. You can either apply a single function or an array of
    // methods to it. If one of them returns with a promise, WebdriverIO will wait until that promise got
    // resolved to continue.
    /**
     * Gets executed once before all workers get launched.
     * @param {Object} config wdio configuration object
     * @param {Array.<Object>} capabilities list of capabilities details
     */
    onPrepare: function (config, capabilities) {
        let vault_suites_dir = 'tests/defaults/test_vault_suites';   

        (async ()=>{
            try {
                fse.emptyDirSync('tests/specs_gen')
                const files = await fs.promises.readdir( vault_suites_dir );

                // Loop them all with the new for...of
                for( const file of files ) {                    
                    // Get the full paths
                    const fromPath = path.join( vault_suites_dir, file );
        
                    // Stat the file to see if we have a file or dir
                    const stat = await fs.promises.stat( fromPath );
                    
                    if( stat.isDirectory() ) {
                        if(file[0] == 'n' && file[1] == 'g' && file[2] == '_') {
                            // No Auto Generation flag is set on folder
                            // Dont generate spec file
                            console.log( `'%s' is a directory. But Skipping specs generation`, fromPath );
                            continue;
                        }
                        console.log( `'%s' is a directory. Making tests/specs/${file}.e2e.ts`, fromPath );
                        fs.copyFile("tests/defaults/specs/template.e2e.ts", `tests/specs_gen/${file}.e2e.ts`, (err) => {
                            if (err) {
                              console.log(`Error on trying to make specs test file ${file}:`, err);
                            }
                        });
                    }
                } // End for...of
            }
            catch( e ) {
                console.error( "We've thrown! Whoops!", e );
            }        
        })(); // Wrap in parenthesis and call now
    },
    /**
     * Gets executed before a worker process is spawned and can be used to initialise specific service
     * for that worker as well as modify runtime environments in an async fashion.
     * @param  {String} cid      capability id (e.g 0-0)
     * @param  {[type]} caps     object containing capabilities for session that will be spawn in the worker
     * @param  {[type]} specs    specs to be run in the worker process
     * @param  {[type]} args     object that will be merged with the main configuration once worker is initialized
     * @param  {[type]} execArgv list of string arguments passed to the worker process
     */
    onWorkerStart: function (cid, caps, specs, args, execArgv) {
        // console.log('onWorkerStart : ' + specs);
        specs.forEach(spec => {
            let test_name = (path.basename(spec) as string).split('.')[0];
            try {
                fs.mkdir(`logs/${test_name}`, { recursive: true }, (err) => {
                    if (err) {
                        console.log(`Error on trying to make logs test folder ${test_name}:`, err);
                    }
                });
            }
            catch( e ) {
                console.error( "We've thrown! Whoops!", e );
            }            
        });
    },
    /**
     * Gets executed just after a worker process has exited.
     * @param  {String} cid      capability id (e.g 0-0)
     * @param  {Number} exitCode 0 - success, 1 - fail
     * @param  {[type]} specs    specs to be run in the worker process
     * @param  {Number} retries  number of retries used
     */
    onWorkerEnd: function (cid, exitCode, specs, retries) {
        // TODO: Maybe we can do the last spec file's test delay here ?
        (async () => {
            try {
                let test_outputs_dir = 'tests/test_config/.local/share/test_outputs';                
                const files = await fs.promises.readdir( test_outputs_dir );

                // Loop them all with the new for...of
                for( const file of files ) {
                    // Get the full paths
                    const fromPath = path.join( test_outputs_dir, file );
        
                    // Stat the file to see if we have a file or dir
                    const stat = await fs.promises.stat( fromPath );
        
                    if( stat.isDirectory() ) {
                        console.log( `'%s' is a test_output directory. Moving for further python tests`, fromPath );
                        fse.move(fromPath, `tests/test_outputs/${file}`, { overwrite: true }, err => {
                            if (err) {
                                console.log(`Error on trying to copying test_output of ${file}:`, err);
                            }
                        })
                    }
                } // End for...of
            }
            catch( e ) {
                console.error( "We've thrown! Whoops!", e );
            }  
        })(); // Wrap in parenthesis and call now
    },
    /**
     * Gets executed just before initialising the webdriver session and test framework. It allows you
     * to manipulate configurations depending on the capability or spec.
     * @param {Object} config wdio configuration object
     * @param {Array.<Object>} capabilities list of capabilities details
     * @param {Array.<String>} specs List of spec file paths that are to be run
     * @param {String} cid worker id (e.g. 0-0)
     */
    // beforeSession: function (config, capabilities, specs, cid) {
    // },
    /**
     * Gets executed before test execution begins. At this point you can access to all global
     * variables like `browser`. It is the perfect place to define custom commands.
     * @param {Array.<Object>} capabilities list of capabilities details
     * @param {Array.<String>} specs        List of spec file paths that are to be run
     * @param {Object}         browser      instance of created browser/device session
     */
    // before: function (capabilities, specs) {
    // },
    /**
     * Runs before a WebdriverIO command gets executed.
     * @param {String} commandName hook command name
     * @param {Array} args arguments that command would receive
     */
    // beforeCommand: function (commandName, args) {
    // },
    /**
     * Hook that gets executed before the suite starts
     * @param {Object} suite suite details
     */
    // beforeSuite: function (suite) {
    // },
    /**
     * Function to be executed before a test (in Mocha/Jasmine) starts.
     */
    // beforeTest: function (test, context) {
    // },
    /**
     * Hook that gets executed _before_ a hook within the suite starts (e.g. runs before calling
     * beforeEach in Mocha)
     */
    // beforeHook: function (test, context) {
    // },
    /**
     * Hook that gets executed _after_ a hook within the suite starts (e.g. runs after calling
     * afterEach in Mocha)
     */
    // afterHook: function (test, context, { error, result, duration, passed, retries }) {
    // },
    /**
     * Function to be executed after a test (in Mocha/Jasmine only)
     * @param {Object}  test             test object
     * @param {Object}  context          scope object the test was executed with
     * @param {Error}   result.error     error object in case the test fails, otherwise `undefined`
     * @param {Any}     result.result    return object of test function
     * @param {Number}  result.duration  duration of test
     * @param {Boolean} result.passed    true if test has passed, otherwise false
     * @param {Object}  result.retries   informations to spec related retries, e.g. `{ attempts: 0, limit: 0 }`
     */
    // afterTest: function(test, context, { error, result, duration, passed, retries }) {
    // },


    /**
     * Hook that gets executed after the suite has ended
     * @param {Object} suite suite details
     */
    // afterSuite: function (suite) {
    // },
    /**
     * Runs after a WebdriverIO command gets executed
     * @param {String} commandName hook command name
     * @param {Array} args arguments that command would receive
     * @param {Number} result 0 - command success, 1 - command error
     * @param {Object} error error object if any
     */
    // afterCommand: function (commandName, args, result, error) {
    // },
    /**
     * Gets executed after all tests are done. You still have access to all global variables from
     * the test.
     * @param {Number} result 0 - test pass, 1 - test fail
     * @param {Array.<Object>} capabilities list of capabilities details
     * @param {Array.<String>} specs List of spec file paths that ran
     */
    // after: function (result, capabilities, specs) {
    // },
    /**
     * Gets executed right after terminating the webdriver session.
     * @param {Object} config wdio configuration object
     * @param {Array.<Object>} capabilities list of capabilities details
     * @param {Array.<String>} specs List of spec file paths that ran
     */
    // afterSession: function (config, capabilities, specs) {
    // },
    /**
     * Gets executed after all workers got shut down and the process is about to exit. An error
     * thrown in the onComplete hook will result in the test run failing.
     * @param {Object} exitCode 0 - success, 1 - fail
     * @param {Object} config wdio configuration object
     * @param {Array.<Object>} capabilities list of capabilities details
     * @param {<Object>} results object containing test results
     */
    // onComplete: function(exitCode, config, capabilities, results) {
    // },
    /**
    * Gets executed when a refresh happens.
    * @param {String} oldSessionId session ID of the old session
    * @param {String} newSessionId session ID of the new session
    */
    // onReload: function(oldSessionId, newSessionId) {
    // }
}
