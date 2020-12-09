// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import { ext } from "./extensionVariables";
import {analyzeContract} from "./commands/analyzeContract";
import {analyzeContractWithoutCompile} from "./commands/analyzeContractWithoutCompile";
import {ItemProvider} from "./utils/itemProvider";
import {getFileContent} from "./utils/getFileContent";
import {postStringRequest} from "./utils/httpUtils";
import {GetContextualAutoCompleteByGlobalVariable} from "./utils/Apicompletion";

let diagnosticsCollection: vscode.DiagnosticCollection;

// this method is called when your extension is activated
// your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
	let recommendEnabled: boolean = true;
	ext.context = context;
	ext.outputChannel = vscode.window.createOutputChannel("SCStudio");

	diagnosticsCollection = vscode.languages.createDiagnosticCollection('scstudio');

	// Use the console to output diagnostic information (console.log) and errors (console.error)
	// This line of code will only be executed once when your extension is activated
	console.log('Congratulations, your extension "SCStudio" is now active!');
	let solidityExt = vscode!.extensions!.getExtension('JuanBlanco.solidity')!;
	solidityExt.activate();

	// vscode.commands.executeCommand('ErrorLens.disable');

	// The command has been defined in the package.json file
	// Now provide the implementation of the command with registerCommand
	// The commandId parameter must match the command field in package.json
	let analyzeSub = vscode.commands.registerCommand('scstudio.analyzecontract', async () => {
		analyzeContract(diagnosticsCollection, vscode.window!.activeTextEditor!.document.uri,vscode.window!.activeTextEditor!.document);
	});

	let analyzeSubWithoutCompiler = vscode.commands.registerCommand('scstudio.analyzeContractWithoutCompile', async () => {
		analyzeContractWithoutCompile(diagnosticsCollection, vscode.window!.activeTextEditor!.document.uri,vscode.window!.activeTextEditor!.document);
	});
 
	let disprovideStatement = vscode.commands.registerCommand('scstudio.disablerecommand', () => {
		recommendEnabled = false;
	}); 
	let provideStatement = vscode.commands.registerCommand('scstudio.enablerecommand', () => {
		recommendEnabled = true;
	}); 

    // context.subscriptions.push(solPv);
	context.subscriptions.push(analyzeSub);
	context.subscriptions.push(analyzeSubWithoutCompiler);
	context.subscriptions.push(provideStatement);
	context.subscriptions.push(disprovideStatement);

	let demoProvider = new ItemProvider([],[]);
	let solPv = vscode.languages.registerCompletionItemProvider("solidity", demoProvider, '.', ' ', '\n');  
	context.subscriptions.push(solPv);
	

	if(recommendEnabled) {
		vscode.workspace.onDidChangeTextDocument(async function(event) {
			// demoProvider.Items = [];
			// demoProvider.codeComs = [];

			if(event.contentChanges[0]) {
				var s = event.contentChanges[0].text;

				/* Token Suggestion */
				if(s === ' ') {
					// vscode.Range.arguments
					console.log('Space trigger.');
				}
				
				/* API Completion */
				else if(s === '.') {
					// vscode.Range.arguments
					console.log('Dot trigger.');
					if(event.contentChanges[0].range) {
						// if (demoProvider.Items === []) {
							let range = event.contentChanges[0].range;
							let str_range = JSON.stringify(range);
							let json_range = JSON.parse(str_range);
							let currentLine = json_range[0].line + 1;
							let currentSen = vscode.window.activeTextEditor?.document.lineAt(currentLine - 1).text;
							let codes : string[];
							codes = [];
							let start = 0;
							if (currentSen) {
								for(let i = 0;;i++) {
									if(currentSen[i] === '.') {
										start = i;
										break;
									}
								}
								const globalVariableContext = GetContextualAutoCompleteByGlobalVariable(currentSen, start);

								demoProvider.Items = globalVariableContext;
								demoProvider.codeComs = [];
							}
						// }
					}
				}
			}
		});
	}
}

// this method is called when your extension is deactivated
export function deactivate() {
	// if (!client) {
    //     return undefined;
    // }
	// return client.stop();
	console.log("See You Again !");
}
