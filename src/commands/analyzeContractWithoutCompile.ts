import * as vscode from 'vscode'
import { getFileContent } from '../utils/getFileContent'
import { getRequest, postRequest } from '../utils/httpUtils'
import { checkPlatform, updateDiagnostics } from '../utils/generateReports'

const os = require('os')
const { window } = vscode

export async function analyzeContractWithoutCompile(
    diagnosticCollection: vscode.DiagnosticCollection,
    fileUri: vscode.Uri,
    dc: vscode.TextDocument
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
        // console.log(vscode.languages.getDiagnostics())
        // vscode.
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

         // Input Time
         let inputOptions : vscode.InputBoxOptions =
         {
             prompt:"Please input the maximum time for analysis.",
             placeHolder: "Input an integer (Default value is 60)"
         };
         let inputTime = 60;
         await vscode.window.showInputBox(inputOptions).then(value =>{
             if(!value)
                 return;
             else
                 inputTime = Number(value);
         });

        vscode.window
            .showInformationMessage(
                `Your analysis has been submitted! Wait for vscode linting`,
                'Dismiss',
            )
            .then((x) => {
                return
            })

        diagnosticCollection.clear();

        // console.log(fileUri)
        const uri = '49.235.239.68:9090/contract';
        let curname = contractName + Date.parse(new Date().toString());
        // set two minutes as a limit duration of testing
        const respBody = await postRequest(uri,{name:curname,contractcode:fileContent,limit:inputTime});
        updateDiagnostics(dc, diagnosticCollection, respBody, fileUri);   
                                
        if (!respBody) {
            vscode.window.showInformationMessage(
                `SCStudio: No security issues found in your contract.`,
            );
        } else {
            vscode.window.showWarningMessage(
                `SCStudio: found some security issues with your contract. Please check the file vulnerabilities.html for detail`,
            );
        }
        
    } catch (err) {
        vscode.window.showErrorMessage(`SCStudio: ${err}`);
    }
}

