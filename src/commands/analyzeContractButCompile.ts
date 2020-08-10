import * as vscode from 'vscode'
import { getFileContent } from '../utils/getFileContent'
import { getRequest, postRequest } from '../utils/httpUtils'
import { getContractName } from '../utils/getContractName'
import fs = require('fs');
import { detailItem, detailPrefix, detailSuffix, tablePrefix, tableSuffix, tableItem } from './ReportTemplate';


const os = require('os')
const { window } = vscode

export async function analyzeContractButCompile(
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
        // const contractName = await getContractName(
        //     fileUri,
        // )

        let FILEPATH = fileUri.fsPath;
        var indexStart = Math.max(FILEPATH.lastIndexOf('\\'), FILEPATH.lastIndexOf('/'));
        var indexEnd = FILEPATH.lastIndexOf('.');
        var strLen = (indexEnd - indexStart) - 1;
        const contractName = FILEPATH.substr(indexStart + 1, strLen);
        console.log(FILEPATH, contractName)

        // Windows OS hack
        if (os.platform() === 'win32') {
            FILEPATH = FILEPATH.replace(/\\/g, '/');
            if (FILEPATH.charAt(0) === '/') {
                FILEPATH = FILEPATH.substr(1);
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
                `SCStudio: found some security issues with your contract. Please check the file vulnerabilities.txt for detail`,
            );
        }
        
    } catch (err) {
        vscode.window.showErrorMessage(`SCStudio: ${err}`);
    }
}

function updateDiagnostics(document: vscode.TextDocument | undefined, collection: vscode.DiagnosticCollection, obj:any, fileUri:any): void {
    let diagnostics: vscode.Diagnostic[] = [];
    let FILEPATH = fileUri.fsPath;
    
    if (os.platform() === 'win32') {
        FILEPATH = FILEPATH.replace(/\\/g, '/')
        if (FILEPATH.charAt(0) === '/') {
            FILEPATH = FILEPATH.substr(1)
        }
    }
    // console.log('FILEPATH  '+FILEPATH)
    let htmlPath = FILEPATH;
    let datetime = new Date();
    var y = datetime.getFullYear();
    var m = datetime.getMonth()+1;
    var d = datetime.getDate();
    var h = datetime.getHours();
    var mm = datetime.getMinutes();
    var s = datetime.getSeconds();
    let dateString = y.toString() + m.toString() + d.toString() + '_' + h.toString() + mm.toString() + s.toString();
    FILEPATH = FILEPATH.substring(0,FILEPATH.lastIndexOf('/')) + '/vulnerabilitiesInfo_' + dateString + '.txt';
    htmlPath = htmlPath.substring(0,FILEPATH.lastIndexOf('/')) + '/vulnerabilitiesReport_' + dateString + '.html';
    if (document) {
        // console.log(document.uri)
        vscode.languages.getDiagnostics(document.uri).slice(1,1);
        obj = JSON.parse(JSON.stringify(obj.text));
        let json_res = JSON.parse(obj);
        console.log(json_res);
        
        // the HTML page
        let detailHtml = detailPrefix;
        let tableHtml = tablePrefix;

        for(var ent in json_res.vulnerabilities) {
            // console.log(ent)
            if(json_res.vulnerabilities[ent]) {
                let message = `Name: ` + json_res.vulnerabilities[ent].name;
                // write the detail information into the file
                let details = `Name:` + json_res.vulnerabilities[ent].name + '\n' +
                    `Description:` + json_res.vulnerabilities[ent].description + '\n' +
                    `SwcID:` + json_res.vulnerabilities[ent].swcId + '\n' +
                    `Advice:` + json_res.vulnerabilities[ent].advice + '\n' +
                    `Line:` + json_res.vulnerabilities[ent].lineNo[0] + '\n' +
                    `Level:` + json_res.vulnerabilities[ent].level + '\n' + '\n';

                // Generate the detail html sector of the current vulnerability
                let curDetail=detailItem.replace(/!NAME!/, json_res.vulnerabilities[ent].name);
                curDetail = curDetail.replace(/!DESCRIPTION!/, json_res.vulnerabilities[ent].description);
                curDetail = curDetail.replace(/!SWCID!/, json_res.vulnerabilities[ent].swcId);
                curDetail = curDetail.replace(/!ADVICE!/, json_res.vulnerabilities[ent].advice);
                curDetail = curDetail.replace(/!LINE!/, json_res.vulnerabilities[ent].lineNo[0]);
                curDetail = curDetail.replace(/!LEVEL!/, json_res.vulnerabilities[ent].level);
                curDetail = curDetail.replace(/SOURCECODE/, document.lineAt(json_res.vulnerabilities[ent].lineNo[0]-1).text);
                detailHtml = detailHtml + curDetail;

                // Generate the table html sector of the current vulnerability
                let tableItemHtml = tableItem.replace(/!NAME!/, json_res.vulnerabilities[ent].name);
                tableItemHtml = tableItemHtml.replace(/!LINE!/, json_res.vulnerabilities[ent].lineNo[0]);
                tableItemHtml = tableItemHtml.replace(/!LEVEL!/, json_res.vulnerabilities[ent].level);
                tableHtml = tableHtml+tableItemHtml;

                // console.log(details)
                // console.log(FILEPATH)
                fs.writeFile(FILEPATH, details, function (err) {
                    if (err)
                        throw err;
                });

                
                let range = document.lineAt(json_res.vulnerabilities[ent].lineNo[0]-1).range;
                let severity : any;
                severity = json_res.vulnerabilities[ent].level;
                if (severity === 'error') {
                    severity = vscode.DiagnosticSeverity.Warning;
                }
                else {
                    severity = vscode.DiagnosticSeverity.Error;
                }
                // severity = vscode.DiagnosticSeverity.Error;
                // let relatedInformation = ''
                let diagnostic = new vscode.Diagnostic(range, message, severity);
                diagnostics.push(diagnostic);
            }
        }
        tableHtml = tableHtml + tableSuffix;
        detailHtml = detailHtml + detailSuffix;
        let html = tableHtml + detailHtml;
        fs.writeFile(htmlPath, html, function (err) {
            if (err)
                throw err;
        });

        console.log("Security Analyze With Complier Finish.");
        collection.set(document.uri, diagnostics);
	} else {
		collection.clear();
	}
}


