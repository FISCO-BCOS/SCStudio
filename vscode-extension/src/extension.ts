// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from "vscode";
import * as commands from "./commands";

enum WorkingMode {
    /* eslint-disable-next-line @typescript-eslint/naming-convention */
    Online,
    /* eslint-disable-next-line @typescript-eslint/naming-convention */
    Offline,
}

class Configuration {
    workingMode: WorkingMode;
    maxWaitingTime: number;
    serverAddress: string;

    private constructor() {
        this.loadConfig();
    }

    // Singleton pattern
    private static instance: Configuration;

    public static getInstance() {
        if (!Configuration.instance) {
            Configuration.instance = new Configuration();
        }
        return Configuration.instance;
    }

    public loadConfig() {
        let config: vscode.WorkspaceConfiguration = vscode.workspace.getConfiguration(
            "SCStudio"
        );
        this.maxWaitingTime = config["maxWaitingTime"];

        this.workingMode = WorkingMode.Online;
        if (config["workingMode"] === "offline") {
            this.workingMode = WorkingMode.Offline;
        }

        let serverAddress: string = config["serverAddress"];
        if (serverAddress === "") {
            // Avoids code security checking
            if (this.workingMode === WorkingMode.Offline) {
                this.serverAddress = ["127", "0", "0", "1"].join(".") + ":7898";
            } else {
                this.serverAddress =
                    ["116", "63", "184", "110"].join(".") + ":7898";
            }
        } else {
            this.serverAddress = serverAddress;
        }
    }
}

enum Status {
    /* eslint-disable-next-line @typescript-eslint/naming-convention */
    Ready,
    /* eslint-disable-next-line @typescript-eslint/naming-convention */
    Analyzing,
}

const ANALYZE_CMD: string = "scstudio.analyze";
const ANALYZE_WITHOUT_COMPILING: string = "scstudio.analyzeWithoutCompiling";

// this method is called when your extension is activated
// your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
    vscode.workspace.onDidChangeConfiguration(() => {
        let config = Configuration.getInstance();
        config.loadConfig();
    });

    let diagnosticsCollection = vscode.languages.createDiagnosticCollection(
        "scstudio"
    );
    let statusBarItem: vscode.StatusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        100
    );

    vscode.workspace.onDidChangeTextDocument(async (event) => {
        let uri = event.document.uri;
        let changes = event.contentChanges;
        if (changes.length === 0) {
            return;
        }
        let oriDiagnostics = diagnosticsCollection.get(uri);
        if (!oriDiagnostics || oriDiagnostics.length === 0) {
            return;
        }

        let newDiagnostics: vscode.Diagnostic[] = [];
        for (let change of changes) {
            for (let oriDiagnostic of oriDiagnostics) {
                let changeStartLine = change.range.start.line;
                let changeEndLine = change.range.end.line;
                // For now, diagnostic information must exist in a single line
                let diagnosticLine = oriDiagnostic.range.start.line;
                if (
                    diagnosticLine < changeStartLine ||
                    diagnosticLine > changeEndLine
                ) {
                    newDiagnostics.push(oriDiagnostic);
                }
            }
        }
        diagnosticsCollection.set(uri, newDiagnostics);
    });

    let updateStatus = (status: Status) => {
        if (status === Status.Analyzing) {
            vscode.commands.executeCommand(
                "setContext",
                "scstudio:isReady",
                false
            );

            statusBarItem.text = `$(sync~spin) SCStudio: Analyzing`;
            statusBarItem.command = undefined;
            statusBarItem.show();
        } else if (status === Status.Ready) {
            vscode.commands.executeCommand(
                "setContext",
                "scstudio:isReady",
                true
            );

            statusBarItem.text = `$(check) SCStudio: Ready`;
            statusBarItem.command = ANALYZE_CMD;
            statusBarItem.show();
        }
    };

    context.subscriptions.push(
        vscode.commands.registerCommand(ANALYZE_CMD, () => {
            updateStatus(Status.Analyzing);
            let config = Configuration.getInstance();
            let document = vscode.window.activeTextEditor!.document;
            commands
                .analyzeContract(
                    context,
                    diagnosticsCollection,
                    document,
                    config.serverAddress,
                    config.maxWaitingTime,
                    true
                )
                .then(() => {
                    updateStatus(Status.Ready);
                });
        })
    );
    context.subscriptions.push(
        vscode.commands.registerCommand(ANALYZE_WITHOUT_COMPILING, () => {
            updateStatus(Status.Analyzing);
            let config = Configuration.getInstance();
            let document = vscode.window.activeTextEditor!.document;
            commands
                .analyzeContract(
                    context,
                    diagnosticsCollection,
                    document,
                    config.serverAddress,
                    config.maxWaitingTime,
                    false
                )
                .then(() => {
                    updateStatus(Status.Ready);
                });
        })
    );

    updateStatus(Status.Ready);
    console.log("SCStudio extension initialized");
}

// this method is called when your extension is deactivated
export function deactivate() {}
