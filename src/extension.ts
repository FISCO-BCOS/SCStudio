// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import { ext } from "./extensionVariables";
import {analyzeContract} from "./commands/analyzeContract";
import {ItemProvider} from "./utils/itemProvider";
import {getFileContent} from "./utils/getFileContent";
import {postStringRequest} from "./utils/httpUtils";


let diagnosticsCollection: vscode.DiagnosticCollection

// this method is called when your extension is activated
// your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
	let recommendEnabled: boolean = true;
	ext.context = context;
	ext.outputChannel = vscode.window.createOutputChannel("SmartIDE");

	diagnosticsCollection = vscode.languages.createDiagnosticCollection('smartide')

	// Use the console to output diagnostic information (console.log) and errors (console.error)
	// This line of code will only be executed once when your extension is activated
	console.log('Congratulations, your extension "secsolidity" is now active!');

	// The command has been defined in the package.json file
	// Now provide the implementation of the command with registerCommand
	// The commandId parameter must match the command field in package.json
	let analyzeSub = vscode.commands.registerCommand('smartide.analyzecontract', async () => {
		// vscode.window.showInformationMessage('Hello World!');
		analyzeContract(diagnosticsCollection, vscode.window!.activeTextEditor!.document.uri,vscode.window!.activeTextEditor!.document)
	});

	// let demoProvider = new ItemProvider();
	// let solPv = vscode.languages.registerCompletionItemProvider("solidity", demoProvider);   
	let disprovideStatement = vscode.commands.registerCommand('smartide.disablerecommand', () => {
		recommendEnabled = false;
	}); 
	let provideStatement = vscode.commands.registerCommand('smartide.enablerecommand', () => {
		recommendEnabled = true;
	}); 
    // context.subscriptions.push(solPv);
	context.subscriptions.push(analyzeSub);
	context.subscriptions.push(provideStatement);
	context.subscriptions.push(disprovideStatement);

	if(recommendEnabled){
		vscode.workspace.onDidChangeTextDocument(async function(event){
			if(event.contentChanges[0]){
				var s = event.contentChanges[0].text
				if(s.charCodeAt(0)===13){
					// vscode.Range.arguments
					console.log('we found the enter key')
					if(event.contentChanges[0].range){
						let range = event.contentChanges[0].range;
						let str_range = JSON.stringify(range);
						let json_range = JSON.parse(str_range);
						let currentLine = json_range[0].line + 1;
						let currentSen = vscode.window.activeTextEditor?.document.lineAt(currentLine - 1).text;
						let curContext = await getFileContent(
							vscode.window!.activeTextEditor!.document.uri,
						)
						// console.log('current line:' + currentLine + " currentSen: "+ currentSen + " curContext: "+curContext)
						// let respBody = await recommend(currentLine, currentSen, curContext);
						// console.log('results: '+JSON.parse(respBody.text).data.results)
						let provider1 = vscode.languages.registerCompletionItemProvider('plaintext', {

							provideCompletionItems(document: vscode.TextDocument, position: vscode.Position, token: vscode.CancellationToken, context: vscode.CompletionContext) {
								// a simple completion item which inserts `Hello World!`
								const simpleCompletion1 = new vscode.CompletionItem('if (msg.gas < 100000) break;');
								let csen = "";
								if(currentSen){
									csen = currentSen;
								}
								const simpleCompletion2 = new vscode.CompletionItem('uint x = accounts[i].balance;');
								const simpleCompletion3 = new vscode.CompletionItem('uint newVal = accounts[i].balance;');
								const simpleCompletion4 = new vscode.CompletionItem('accounts[i].balance += 1;');
								const simpleCompletion5 = new vscode.CompletionItem('break;');
							
								// return all completion items as array
								return [
									simpleCompletion1,
									simpleCompletion2,
									simpleCompletion3,
									simpleCompletion4,
									simpleCompletion5
								];
							}
						});
						context.subscriptions.push(provider1);
					}
				}
			}
		})
	}
}

async function handleChange(event:any) {
	// console.log("Change in the text editor")
	if(event.contentChanges[0]){
		var s = event.contentChanges[0].text
		if(s.charCodeAt(0)===13){
			// vscode.Range.arguments
			console.log('we found the enter key')
			if(event.contentChanges[0].range){
				let range = event.contentChanges[0].range;
				let str_range = JSON.stringify(range);
				let json_range = JSON.parse(str_range);
				let currentLine = json_range[0].line + 1;
				let currentSen = vscode.window.activeTextEditor?.document.lineAt(currentLine - 1).text;
				let curContext = await getFileContent(
					vscode.window!.activeTextEditor!.document.uri,
				)
				// console.log('current line:' + currentLine + " currentSen: "+ currentSen + " curContext: "+curContext)
				let respBody = await recommend(currentLine, currentSen, curContext);
				console.log('results: '+JSON.parse(respBody.text).data.results)
			}
		}
	}
	
    console.log(event);
}

async function recommend(curLen : number, currentSen : any, curContext : string) {
	const uri = '49.235.239.68:9065/predict'
        // set two minutes as a limit duration of testing
        let strjson = JSON.stringify({sentence:currentSen,
        curLine:curLen,
        context:curContext})
        // console.log(JSON.parse(strjson))
        const respBody = await postStringRequest(uri,strjson);
    
        if (!respBody) {
            vscode.window.showInformationMessage(
                `SmartIDE: Error when providing recommend statements.`,
		 
				)
        } 
		console.log(respBody) 
		return respBody;
}

// this method is called when your extension is deactivated
export function deactivate() {}
