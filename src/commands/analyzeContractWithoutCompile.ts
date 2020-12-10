import * as vscode from 'vscode'
import { getFileContent } from '../utils/getFileContent'
import { getRequest, postRequest } from '../utils/httpUtils'
import { checkPlatform, updateDiagnostics } from '../utils/generateReports'

const os = require('os')
const { window } = vscode

export async function analyzeContractWithoutCompile(
    diagnosticCollection: vscode.DiagnosticCollection,
    fileUri: vscode.Uri,
    dc: vscode.TextDocument,
    inputTime: number
): Promise<void> {
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
        var indexEnd = FILEPATH.lastIndexOf('.');
        var strLen = (indexEnd - indexStart) - 1;
        const contractName = FILEPATH.substr(indexStart + 1, strLen);
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
        rootDirectory =
            rootDirectory[rootDirectory.length - 1]

        vscode.window
            .showInformationMessage(
                'Your file has been submitted! The analysis will finish in ' + inputTime.toString() + ' seconds.',
                'Dismiss',
            )
            .then((x) => {
                return
            })

        diagnosticCollection.clear();

        const uri = '49.235.239.68:9090/contract';
        let curname = contractName + Date.parse(new Date().toString());

        const respBody = await postRequest(uri, {name:curname, contractcode:fileContent, limit:inputTime});
                                
        if (!respBody) {
            vscode.window.showInformationMessage(
                'SCStudio: Analysis Failed.',
            );
        } 
        else {
            updateDiagnostics(dc, diagnosticCollection, respBody, fileUri);   
            
            let empty = true;
            Object.keys(respBody.body['vulnerabilities']).forEach(function(key) {
                if (respBody.body['vulnerabilities'][key]) {
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
        
    } catch (err) {
        vscode.window.showErrorMessage(`SCStudio: ${err}`);
    }
}

