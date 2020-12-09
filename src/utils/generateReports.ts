import * as vscode from 'vscode'
import fs = require('fs')
import { detailItem, detailPrefix, detailSuffix, tablePrefix, tableSuffix, tableItem } from '../commands/ReportTemplate';


const os = require('os')
const { window } = vscode

// Windows OS hack
export function checkPlatform(
    FILEPATH: string
): string {
    if (os.platform() === 'win32') {
        FILEPATH = FILEPATH.replace(/\\/g, '/')
        if (FILEPATH.charAt(0) === '/') {
            FILEPATH = FILEPATH.substr(1)
        }
    }
    return FILEPATH;
}

export function updateDiagnostics(document: vscode.TextDocument | undefined, collection: vscode.DiagnosticCollection, obj:any, fileUri:any): void {
    let diagnostics: vscode.Diagnostic[] = [];
    let FILEPATH = checkPlatform(fileUri.fsPath);
    
    let htmlPath = FILEPATH;
    let datetime = new Date();
    // add leading zero for single digit number
    var y = datetime.getFullYear();
    var m = datetime.getMonth() + 1;
    var d = datetime.getDate();
    var h = datetime.getHours();
    var mm = datetime.getMinutes();
    var s = datetime.getSeconds();
    let dateString = y.toString() + m.toString() + d.toString() + '_' + h.toString() + mm.toString() + s.toString();
    let reportFolder = FILEPATH.substring(0, FILEPATH.lastIndexOf('/')) + '/reports/';
    FILEPATH = reportFolder + 'vulnerabilitiesInfo_' + dateString + '.txt';
    htmlPath = reportFolder + 'vulnerabilitiesReport_' + dateString + '.html';
    
    if (document) {
        vscode.languages.getDiagnostics(document.uri).slice(1,1);
        obj = JSON.parse(JSON.stringify(obj.text));
        let json_res = JSON.parse(obj);
        console.log(json_res);
        
        // the HTML page
        let detailHtml = detailPrefix;
        let tableHtml = tablePrefix;

        for(var ent in json_res.vulnerabilities) {
            let respos = json_res.vulnerabilities[ent];
            if(respos) {
                let message = `Name: ` + respos.name;
                // write the detail information into the file
                let details = `Name:` + respos.name + '\n' +
                    `Description:` + respos.description + '\n' +
                    `SwcID:` + respos.swcId + '\n' +
                    `Advice:` + respos.advice + '\n' +
                    `Line:` + respos.lineNo[0] + '\n' +
                    `Level:` + respos.level + '\n' + '\n';

                // Generate the detail html sector of the current vulnerability
                let curDetail=detailItem.replace(/!NAME!/, respos.name);
                curDetail = curDetail.replace(/!DESCRIPTION!/, respos.description);
                curDetail = curDetail.replace(/!SWCID!/, respos.swcId);
                curDetail = curDetail.replace(/!ADVICE!/, respos.advice);
                curDetail = curDetail.replace(/!LINE!/, respos.lineNo[0]);
                curDetail = curDetail.replace(/!LEVEL!/, respos.level);
                curDetail = curDetail.replace(/SOURCECODE/, document.lineAt(respos.lineNo[0]-1).text);
                detailHtml = detailHtml + curDetail;

                // Generate the table html sector of the current vulnerability
                let tableItemHtml = tableItem.replace(/!NAME!/, respos.name);
                tableItemHtml = tableItemHtml.replace(/!LINE!/, respos.lineNo[0]);
                tableItemHtml = tableItemHtml.replace(/!LEVEL!/, respos.level);
                tableHtml = tableHtml+tableItemHtml;
          
                fs.writeFile(FILEPATH, details, function (err) {
                    if (err)
                        throw err;
                });

                let range = document.lineAt(respos.lineNo[0]-1).range;
                
                let severity : any;
                severity = respos.level;
                if (severity === 'error') {
                    severity = vscode.DiagnosticSeverity.Error;
                }
                else {
                    severity = vscode.DiagnosticSeverity.Warning;
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
            console.log(htmlPath)
            if (err)
                throw err;
        });

        console.log("Security Analyze With Complier Finish.");
        collection.set(document.uri, diagnostics);
	} else {
		collection.clear();
	}
}