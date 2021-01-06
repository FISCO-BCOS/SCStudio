import * as vscode from 'vscode'
import fs = require('fs')
import { getFileContent } from '../utils/getFileContent'
import { getRequest, postRequest } from '../utils/httpUtils'
import { checkPlatform, updateDiagnostics } from '../utils/generateReports'

const os = require('os')
const { window } = vscode

export async function analyzeContract(
    diagnosticCollection: vscode.DiagnosticCollection,
    fileUri: vscode.Uri,
    dc: vscode.TextDocument,
    inputTime: number,
    url : string,
    isWebService: boolean
): Promise<void> {
    await vscode!.extensions!
        .getExtension('JuanBlanco.solidity')!
        .activate()
        .then(
            async () => {
                try { 
                    await vscode!.extensions!.getExtension('philhindle.errorlens')!.activate().then(
                        async () => {
                            vscode.commands.executeCommand('ErrorLens.enable');
                        }              
                    );
                    diagnosticCollection.clear();
                    const projectConfiguration: vscode.WorkspaceConfiguration = vscode.workspace.getConfiguration(
                        'scstudiovsc',
                    )

                    let d_original = vscode.languages.getDiagnostics(fileUri)
                    d_original.splice(0,d_original.length)
                    const fileContent = await getFileContent(
                        fileUri,
                    )

                    let FILEPATH = fileUri.fsPath;
                    var indexStart = Math.max(FILEPATH.lastIndexOf('\\'), FILEPATH.lastIndexOf('/'));
                    const filedir = FILEPATH.substring(0,indexStart);
                    var indexEnd = FILEPATH.lastIndexOf('.');
                    var strLen = (indexEnd - indexStart) - 1;
                    const contractName = FILEPATH.substr(indexStart + 1, strLen);
                    const contractType = FILEPATH.substring(indexEnd + 1)
                    console.log(FILEPATH, contractName)

                    FILEPATH = checkPlatform(FILEPATH);

                    // Remove file name from path
                    const rootPath = FILEPATH.substring(
                        0,
                        FILEPATH.lastIndexOf('/'),
                    )

                    let directoryPath = rootPath.replace(/\\/g, '/')
                    let rootDirectory: any = directoryPath.split(
                        '/',
                    )
                    rootDirectory = rootDirectory[rootDirectory.length - 1]
                    
                    const uri = url + '/contract';
                    

                    if(contractType != "sol"){
                            vscode.window.showWarningMessage(
                                'SCStudio: The current file is not a Solidity contract. Please choose a solidity file to analyze.',
                            );  
                    }
                    else{
                        vscode.window
                        .showInformationMessage(
                            'Your file has been submitted! The analysis will finish in ' + inputTime.toString() + ' seconds.',
                            'Dismiss',
                        )
                        diagnosticCollection.clear();

                    const exec  = require("await-exec");
                    let commandline = "docker run    -v /var/run/docker.sock:/var/run/docker.sock    -v /usr/local/bin/docker:/usr/bin/docker    -v "+filedir+":/enTools/contract    -i renardbebe/entools "+contractName+" "+filedir+"  -t "+inputTime

                    
                    let curname = contractName + Date.parse(new Date().toString());
                    let respBody : any;
                    // if the user wants to analyze online
                    if (isWebService){
                        respBody = await (await postRequest(uri, {name:curname, contractcode:fileContent, limit:inputTime}));            
                        respBody = JSON.parse(JSON.stringify(respBody.text));
                    }
                    else{
                    // if the user doesn't want to put his code online
                        await exec(commandline);    
                        const jsonfile = fs.readFileSync(filedir + "/" + contractName + "/finalReport.json","utf8")
                        respBody = JSON.parse(jsonfile)
                    }
                    
                    if (!respBody) {
                        vscode.window.showInformationMessage(
                            'SCStudio: Analysis Failed.',
                        );
                    } 
                    else {
                        
                        updateDiagnostics(dc, diagnosticCollection, respBody, fileUri);     
                        
                        let empty = true;
                        Object.keys(respBody.vulnerabilities).forEach(function(key) {
                            if (respBody.vulnerabilities[key]) {
                                empty = false;
                            }
                       });

                        if (empty) {
                            vscode.window.showInformationMessage(
                                'SCStudio: No security issues found in your contract.',
                            );
                        }
                        else {
                            vscode.window.showWarningMessage(
                                'SCStudio: There are some security issues in your contract. Please check the report (HTML) for detail.',
                            );
                        }
                    }
                }
                } catch (err) {
                    vscode.window.showErrorMessage(`SCStudio: ${err}`);
                }
        }, 
    );
}

