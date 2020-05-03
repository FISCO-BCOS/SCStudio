import * as vscode from 'vscode'
import { getFileContent } from '../utils/getFileContent'
import { getRequest, postRequest } from '../utils/httpUtils'
import { getContractName } from '../utils/getContractName'
import fs = require('fs')


const os = require('os')
const { window } = vscode

export async function analyzeContract(
    diagnosticCollection: vscode.DiagnosticCollection,
    fileUri: vscode.Uri,
    dc: vscode.TextDocument
): Promise<void> {
    await vscode!.extensions!
        .getExtension('JuanBlanco.solidity')!
        .activate()
        .then(
            async () => {
                try { 
                    await vscode!.extensions!.getExtension('philhindle.errorlens')!.activate().then(
                        // async () => {
                        //     vscode.commands.executeCommand('ErrorLens.enable')
                        // }
                        
                    )
                    diagnosticCollection.clear()
                    const projectConfiguration: vscode.WorkspaceConfiguration = vscode.workspace.getConfiguration(
                        'smartidevsc',
                    )
                    // console.log(vscode.languages.getDiagnostics())
                    // vscode.
                    let d_original = vscode.languages.getDiagnostics(fileUri)
                    d_original.splice(0,d_original.length)
                    const fileContent = await getFileContent(
                        fileUri,
                    )
                    const contractName = await getContractName(
                        fileUri,
                    )

                    let FILEPATH = fileUri.fsPath
                    // console.log(dc.uri)

                    // Windows OS hack
                    if (os.platform() === 'win32') {
                        FILEPATH = FILEPATH.replace(/\\/g, '/')
                        if (FILEPATH.charAt(0) === '/') {
                            FILEPATH = FILEPATH.substr(1)
                        }
                    }

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

                    vscode.window
                        .showInformationMessage(
                            `Your analysis has been submitted! Wait for vscode linting`,
                            'Dismiss',
                        )
                        .then((x) => {
                            return
                        })

                    diagnosticCollection.clear()
                    // console.log(fileUri)
                    const uri = '49.235.239.68:9090/contract'                      
                    let curname = contractName + Date.parse(new Date().toString());
                    // set two minutes as a limit duration of testing
                    const respBody = await postRequest(uri,{name:curname,contractcode:fileContent,limit:30});
                    updateDiagnostics(dc, diagnosticCollection, respBody);                     
                    if (!respBody) {
                        vscode.window.showInformationMessage(
                            `SmartIDE: No security issues found in your contract.`,
                        )
                    } else {
                        vscode.window.showWarningMessage(
                            `SmartIDE: found some security issues with your contract. Please check the file vulnerabilities.txt for detail`,
                        )
                    }
                
            } catch (err) {
                vscode.window.showErrorMessage(`SmartIDE: ${err}`)
            }
            }, 
        )
}

function updateDiagnostics(document: vscode.TextDocument | undefined, collection: vscode.DiagnosticCollection, obj:any): void {
    let diagnostics: vscode.Diagnostic[] = [];
    
	if (document) {
        // console.log(document.uri)
        vscode.languages.getDiagnostics(document.uri).slice(1,1);
        obj = JSON.parse(JSON.stringify(obj.text))
        let json_res = JSON.parse(obj)
        console.log(json_res)
        for(var ent in json_res.vulnerabilities){
            // console.log(ent)
            if(json_res.vulnerabilities[ent]){
                let message = `Name: `+json_res.vulnerabilities[ent].name 
                // + `; Description: ` + json_res.vulnerabilities[ent].description;
                let range = document.lineAt(json_res.vulnerabilities[ent].lineNo[0]-1).range;
                
                let severity : any;
                if(json_res.vulnerabilities[ent].swcId == 0){
                    severity = vscode.DiagnosticSeverity.Warning;
                }
                else{
                    severity = vscode.DiagnosticSeverity.Error;
                }
                severity = vscode.DiagnosticSeverity.Error;
                // let relatedInformation = ''
                let diagnostic = new vscode.Diagnostic(range, message, severity);
                diagnostics.push(diagnostic);
            }
        }
        collection.set(document.uri, diagnostics)
	} else {
		collection.clear();
	}
}


