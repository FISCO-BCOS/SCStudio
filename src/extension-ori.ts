// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import { ext } from "./extensionVariables";
import {analyzeContract} from "./commands/analyzeContract";
import {ItemProvider} from "./utils/itemProvider";
import {getFileContent} from "./utils/getFileContent";
import {postStringRequest} from "./utils/httpUtils";
import {GetContextualAutoCompleteByGlobalVariable} from "./utils/Apicompletion";
import superagent = require('superagent');

let diagnosticsCollection: vscode.DiagnosticCollection;

// this method is called when your extension is activated
// your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
	let recommendEnabled: boolean = true;
	ext.context = context;
	ext.outputChannel = vscode.window.createOutputChannel("SmartIDE");

	diagnosticsCollection = vscode.languages.createDiagnosticCollection('smartide');

	// Use the console to output diagnostic information (console.log) and errors (console.error)
	// This line of code will only be executed once when your extension is activated
	console.log('Congratulations, your extension "secsolidity" is now active!');

	// The command has been defined in the package.json file
	// Now provide the implementation of the command with registerCommand
	// The commandId parameter must match the command field in package.json
	let analyzeSub = vscode.commands.registerCommand('smartide.analyzecontract', async () => {
		// vscode.window.showInformationMessage('Hello World!');
		analyzeContract(diagnosticsCollection, vscode.window!.activeTextEditor!.document.uri,vscode.window!.activeTextEditor!.document);
	});
 
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

	// let demoProvider = new ItemProvider([],[]);
	// let solPv = vscode.languages.registerCompletionItemProvider("solidity", demoProvider, '.');  
	// context.subscriptions.push(solPv);

	let solPv_token = vscode.languages.registerCompletionItemProvider
					('solidity', 
					{
						provideCompletionItems,
						resolveCompletionItem
					}, 
					' '); 
	context.subscriptions.push(solPv_token);

	if(recommendEnabled) {
		vscode.workspace.onDidChangeTextDocument(async function(event) {
			// demoProvider.Items = [];
			// demoProvider.codeComs = [];

			if(event.contentChanges[0]) {
				var s = event.contentChanges[0].text;

				/* Statement Suggestion */
				// if(s.charCodeAt(0)===13){
				// 	// vscode.Range.arguments
				// 	console.log('we found the enter key')
				// 	if(event.contentChanges[0].range){
				// 		let range = event.contentChanges[0].range;
				// 		let str_range = JSON.stringify(range);
				// 		let json_range = JSON.parse(str_range);
				// 		let currentLine = json_range[0].line + 1;
				// 		let currentSen = vscode.window.activeTextEditor?.document.lineAt(currentLine - 1).text;
				// 		let curContext = await getFileContent(
				// 			vscode.window!.activeTextEditor!.document.uri,
				// 		)
				// 		// console.log('current line:' + currentLine + " currentSen: "+ currentSen + " curContext: "+curContext)
				// 		let respBody = await recommend(currentLine, currentSen, curContext);
				// 		console.log('results: '+JSON.parse(respBody.text).data.results)
				// 		let res = JSON.parse(respBody.text).data.results
				// 		let codes : string[]
				// 		codes = []
				// 		for(var i in res){
				// 			codes = codes.concat(res[i])
				// 		}
				// 		let demoProvider = new ItemProvider(codes);
				// 		let solPv = vscode.languages.registerCompletionItemProvider("solidity", demoProvider);  
				// 		context.subscriptions.push(solPv);
				// 	}
				// }

				/* Token Suggestion */
				if(s.charCodeAt(0)===32){
					// vscode.Range.arguments
					console.log('we found the space');

					if(event.contentChanges[0].range){
						// let range = event.contentChanges[0].range;
						// let str_range = JSON.stringify(range);
						// let json_range = JSON.parse(str_range);
						// let currentLine = json_range[0].line + 1;
						// let currentSen = vscode.window.activeTextEditor?.document.lineAt(currentLine - 1).text;
						// let curContext = await getFileContent(
						// 	vscode.window!.activeTextEditor!.document.uri,
						// );
						// // console.log('current line:' + currentLine + " currentSen: "+ currentSen + " curContext: "+curContext);
						// let respBody = await recommendToken(currentLine, currentSen, curContext);
						// console.log('results: '+ JSON.parse(respBody.text).data.results);
						// let res = JSON.parse(respBody.text).data.results;
						// let codes : string[];
						// codes = [];
						// for(var i in res) {
						// 	codes = codes.concat(res[i]);
						// }
						// // codes = ['isOwner','returns','public','auth','{'];
						// // console.log('codes: '+ codes);

						// demoProvider.codeComs = codes;
					}
				}
				
				/* API Completion */
				else if(s==='.'){
					// vscode.Range.arguments
					console.log('we found the dot');
					if(event.contentChanges[0].range){
						let range = event.contentChanges[0].range;
						let str_range = JSON.stringify(range);
						let json_range = JSON.parse(str_range);
						let currentLine = json_range[0].line + 1;
						let currentSen = vscode.window.activeTextEditor?.document.lineAt(currentLine - 1).text;
						let codes : string[];
						codes = [];
						let start = 0;
						if (currentSen){
							for(let i = 0;;i++){
								if(currentSen[i] === '.'){
									start = i;
									break;
								}
							}
							const globalVariableContext = GetContextualAutoCompleteByGlobalVariable(currentSen, start);
							// let NormalProvider = new ItemProvider([],globalVariableContext);
							// context.subscriptions.pop()
							// let solnorPv = vscode.languages.registerCompletionItemProvider("solidity", NormalProvider,'.');  
							// context.subscriptions.push(solnorPv);
							let demoProvider = new ItemProvider([],[]);
							let solPv = vscode.languages.registerCompletionItemProvider("solidity", demoProvider,'.');  
							context.subscriptions.push(solPv);

							demoProvider.Items = globalVariableContext;
							demoProvider.codeComs = [];
						}
					}
				}
			}
		});
	}
	// let serverModule = context.asAbsolutePath(
    //     path.join('out', 'server.js')
    // );

    // let serverOptions: ServerOptions = {
    //     module: serverModule, transport: TransportKind.ipc
    // };
}

// async function recommendToken(curLen : number, currentSen : any, curContext : string) {
// 	const uri = '49.235.239.68:9065/tokenPredict';
// 	// set two minutes as a limit duration of testing
// 	let strjson = JSON.stringify({
// 	context:curContext});
// 	// console.log(JSON.parse(strjson))
// 	const respBody = await postStringRequest(uri,strjson);

// 	if (!respBody) {
// 		vscode.window.showInformationMessage(
// 			`SmartIDE: Error when providing recommend statements.`,
// 			);
// 	} 
// 	console.log(respBody); 
// 	return respBody;
// }

function provideCompletionItems(document: vscode.TextDocument, position: vscode.Position, token: vscode.CancellationToken): vscode.CompletionItem[] {
    var previous=document.getText(new vscode.Range(new vscode.Position(0,0), position));
	var cnt=1;
	var jsonObj={"sentence":(previous), "context":(previous)};
	var strjson=JSON.stringify(jsonObj);

	const senUrl = "http://49.235.239.68:9065/tokenPredict";
	var CList=new Array();

	superagent.post(senUrl)
		.send(strjson)
		.end((err: Error, res: superagent.Response) => {
			// console.log('end url:' + url);
			if (!err) {
				var arr=[1,2,3];
				arr=JSON.parse(res.text).data.results;
				for(var it in arr) {
					var temp=new vscode.CompletionItem(it, vscode.CompletionItemKind.Field);
					temp.sortText=cnt.toString();
					CList.push(temp);
					cnt+=1;
				}
				console.log('List:' + arr);

			} else{
				console.log('err:' + err);
			}
		});

	return CList;
}


function resolveCompletionItem(item: vscode.CompletionItem, token: vscode.CancellationToken): any {
	return null;
}

// this method is called when your extension is deactivated
export function deactivate() {
	// if (!client) {
    //     return undefined;
    // }
    // return client.stop();
}
