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
): Promise<void> {
    await vscode!.extensions!
        .getExtension('JuanBlanco.solidity')!
        .activate()
        .then(
            async () => {
                vscode.commands
                    .executeCommand('solidity.compile.active')
                    .then(async (done) => {
                        try {
                            if (!done) {
                                throw new Error(
                                    `SmartIDE: Error with solc compilation.`,
                                )
                            } else {
                                await vscode!.extensions!.getExtension('philhindle.errorlens')!.activate().then(
                                    // async () => {
                                    //     vscode.commands.executeCommand('ErrorLens.enable')
                                    // }
                                )
                                const projectConfiguration: vscode.WorkspaceConfiguration = vscode.workspace.getConfiguration(
                                    'smartidevsc',
                                )
                                
                                const fileContent = await getFileContent(
                                    fileUri,
                                )
                                const contractName = await getContractName(
                                    fileUri,
                                )

                                let FILEPATH = fileUri.fsPath

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
                                rootDirectory =
                                    rootDirectory[rootDirectory.length - 1]

                                vscode.window
                                    .showInformationMessage(
                                        `Your analysis has been submitted! Wait for vscode linting`,
                                        'Dismiss',
                                    )
                                    .then((x) => {
                                        return
                                    })

                                diagnosticCollection.clear()
                                const uri = '49.235.239.68:9090/contract'
                                
                                let dc = vscode.window.activeTextEditor?.document
                                let curname = contractName + Date.parse(new Date().toString());
                                // set two minutes as a limit duration of testing
                                const respBody = await postRequest(uri,{name:curname,contractcode:fileContent,limit:120});
                                // const respBody = {vulnerabilities: {
                                //     ent1: {
                                //         name: "Function Default Visibility",
                                //         description: "Functions that do not have a function visibility type specified are public by default. This can lead to a vulnerability if a developer forgot to set the visibility and a malicious user is able to make unauthorized or unintended state changes.",
                                //         swcId: 100,
                                //         advice: "Functions can be specified as being external, public, internal or private. It is recommended to make a conscious decision on which visibility type is appropriate for a function. This can dramatically reduce the attack surface of a contract system.",
                                //         lineNo: [
                                //             6
                                //         ]
                                //     },
                                //     ent2: null,
                                //     ent3: {
                                //         name: "Call-stack Depth Limit Exceeding",
                                //         description: "The Ethereum Virtual Machine implementation limits the call-stack's depth to 1024 frames. The call-stack's depth increases by one if a contract calls another via the send or call instruction. This opens an attack vector to deliberately cause the send instruction to fail.",
                                //         swcId: 0,
                                //         advice: "Specifically, an attacker can prepare a contract to call itself 1023 times before sending a transaction to KoET to claim the throne from the current king. Thus, the attacker ensures that the call-stack's depth of KoET reaches 1024, causing the send instruction in Line 15 to fail. As the result, the current king will not receive any payment.",
                                //         lineNo: [
                                //             13
                                //         ]
                                //     }}};
                                // console.log(respBody)

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
                            }
                        } catch (err) {
                            vscode.window.showErrorMessage(`SmartIDE: ${err}`)
                        }
                    })
            },
            (err) => {
                throw new Error(`SmartIDE: Error with solc compilation. ${err}`)
            },
        )
}

function updateDiagnostics(document: vscode.TextDocument | undefined, collection: vscode.DiagnosticCollection, obj:any): void {
    let diagnostics: vscode.Diagnostic[] = [];
	if (document) {
        console.log(vscode.languages.getDiagnostics(document.uri))
        vscode.languages.getDiagnostics(document.uri).slice(1,1);
        console.log(vscode.languages.getDiagnostics(document.uri))
        for(var ent in obj.vulnerabilities){
            if(obj.vulnerabilities[ent]){
                let message = `Name: `+obj.vulnerabilities[ent].name + `; Description: ` + obj.vulnerabilities[ent].description;
                let range = document.lineAt(obj.vulnerabilities[ent].lineNo-1).range;
                
                let severity : any;
                if(obj.vulnerabilities[ent].swcId == 0){
                    severity = vscode.DiagnosticSeverity.Warning;
                }
                else{
                    severity = vscode.DiagnosticSeverity.Error;
                }
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


