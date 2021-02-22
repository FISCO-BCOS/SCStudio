import * as vscode from "vscode";
import path = require("path");
import strftime = require("strftime");
import fs = require("fs");
import ejs = require("ejs");
import { postRequest } from "../common";

interface Vulnerability {
    advice: string;
    description: string;
    level: string;
    lineNo: number[];
    name: string;
    swcId: string;
}

interface Response {
    msg: string;
    status: number;
    vulnerabilities: Map<string, Vulnerability>;
}

function updateDiagnostics(
    document: vscode.TextDocument,
    diagnosticCollection: vscode.DiagnosticCollection,
    vulnerabilities: Vulnerability[]
) {
    let diagnostics: vscode.Diagnostic[] = [];
    for (let vulnerability of vulnerabilities) {
        let advice: string;
        if (!vulnerability.advice) {
            advice = "null";
        } else {
            advice = vulnerability.advice;
        }

        let swcId: string;
        if (!vulnerability.swcId) {
            swcId = "null";
        } else {
            swcId = vulnerability.swcId;
        }
        let message = `(SCStudio) ${vulnerability.name}
- Description
  ${vulnerability.description}
- Advice
  ${advice}
- SWC ID
  ${swcId}`;
        let severity = vscode.DiagnosticSeverity.Error;
        if (vulnerability.level !== "error") {
            severity = vscode.DiagnosticSeverity.Warning;
        }

        for (let line of vulnerability.lineNo) {
            let range = document.lineAt(line - 1).range;
            let diagnostic = new vscode.Diagnostic(range, message, severity);
            diagnostics.push(diagnostic);
        }
    }

    diagnosticCollection.set(document.uri, diagnostics);
}

export async function analyzeContract(
    context: vscode.ExtensionContext,
    diagnosticCollection: vscode.DiagnosticCollection,
    document: vscode.TextDocument,
    serverAddress: string,
    timeout: number,
    needCompiling: boolean
) {
    if (needCompiling) {
        await vscode.extensions.getExtension("JuanBlanco.solidity")!.activate();
    }

    await vscode.extensions
        .getExtension("philhindle.errorlens")!
        .activate()
        .then(() => {
            vscode.commands.executeCommand("ErrorLens.enable");
        });

    diagnosticCollection.clear();
    let originalDiagnostics = vscode.languages.getDiagnostics(document.uri);
    // Clear original diagnostics, this method can be referenced at
    // https://stackoverflow.com/questions/1232040/how-do-i-empty-an-array-in-javascript
    originalDiagnostics.splice(0, originalDiagnostics.length);

    vscode.window.showInformationMessage(
        `This contract had been submitted to analysis.`,
        "Dismiss"
    );

    let respBody: Response;
    try {
        let data = {
            content: document.getText(),
            timeout,
        };
        respBody = await postRequest("contract_analysis", serverAddress, data);
    } catch (error) {
        vscode.window.showErrorMessage(
            `SCStudio: Unable to reach backend server, due to \`${error.message}\``
        );
        return;
    }

    if (Object.keys(respBody!.vulnerabilities).length === 0) {
        vscode.window.showInformationMessage(
            "SCStudio: No security issues detected in this contract.",
            "Dismiss"
        );
        return;
    }

    let vulnerabilities: Vulnerability[] = Object.values(
        respBody!.vulnerabilities
    );
    updateDiagnostics(document, diagnosticCollection, vulnerabilities);
    vscode.window
        .showWarningMessage(
            "SCStudio: Some security issues detected in this contract. Do you need to export the HTML report to local?",
            "Yes",
            "No"
        )
        .then((selection) => {
            if (selection === "Yes") {
                vscode.window
                    .showOpenDialog({
                        canSelectFiles: false,
                        canSelectFolders: true,
                        canSelectMany: false,
                        title: "Select a location to store the report",
                    })
                    .then((uri) => {
                        if (uri !== undefined) {
                            let dir = uri[0].fsPath;
                            let date = strftime("%Y%m%d%H%M%S", new Date());
                            let filePath = path.join(
                                dir,
                                `VulnerabilitiesReport_${date}.html`
                            );

                            let codeLines = document.getText().split("\n");
                            let resourcePath = path.join(
                                context.extensionPath,
                                "static"
                            );

                            ejs.renderFile(
                                path.join(
                                    resourcePath,
                                    "template",
                                    "report.ejs"
                                ),
                                {
                                    resourcePath,
                                    vulnerabilities,
                                    codeLines,
                                }
                            ).then((htmlReport) => {
                                fs.writeFileSync(filePath, htmlReport);
                                // Create and show panel
                                const panel = vscode.window.createWebviewPanel(
                                    "Analysis Report",
                                    "Analysis Report",
                                    vscode.ViewColumn.One,
                                    {}
                                );

                                // And set its HTML content
                                panel.webview.html = htmlReport;
                            });
                        }
                    });
            }
        });
}
