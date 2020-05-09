// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import { ext } from "./extensionVariables";
import {analyzeContract} from "./commands/analyzeContract";
import {ItemProvider} from "./utils/itemProvider";
import {getFileContent} from "./utils/getFileContent";
import {postStringRequest} from "./utils/httpUtils";
import {GetContextualAutoCompleteByGlobalVariable} from "./utils/Apicompletion"

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
	let demoProvider = new ItemProvider([],[]);
	let solPv = vscode.languages.registerCompletionItemProvider("solidity", demoProvider,'.',' ');  
	context.subscriptions.push(solPv);

	if(recommendEnabled){
		vscode.workspace.onDidChangeTextDocument(async function(event){
			if(event.contentChanges[0]){
				var s = event.contentChanges[0].text
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

				if(s.charCodeAt(0)===32){
					// vscode.Range.arguments
					console.log('we found the space')
					demoProvider.Items = [];
					demoProvider.codeComs = [];
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
						let respBody = await recommendToken(currentLine, currentSen, curContext);
						console.log('results: '+JSON.parse(respBody.text).data.results)
						let res = JSON.parse(respBody.text).data.results
						let codes : string[]
						codes = []
						for(var i in res){
							codes = codes.concat(res[i])
						}
						// codes = ['isOwner','returns','public','auth','{']
						// let demoProvider1 = new ItemProvider(codes,[]);
						// context.subscriptions.pop();
						demoProvider.codeComs = codes;
						
						// let solPv = vscode.languages.registerCompletionItemProvider("solidity", demoProvider);
						// context.subscriptions.push(solPv);
					}
				}
				if(s.charCodeAt(0)===46){
					// vscode.Range.arguments
					console.log('we found the dot')
					if(event.contentChanges[0].range){
						let range = event.contentChanges[0].range;
						let str_range = JSON.stringify(range);
						let json_range = JSON.parse(str_range);
						let currentLine = json_range[0].line + 1;
						let currentSen = vscode.window.activeTextEditor?.document.lineAt(currentLine - 1).text;
						let codes : string[]
						codes = []
						let start = 0
						if (currentSen){
							for(let i = 0;;i++){
								if(currentSen[i] == '.'){
									start = i
									break;
								}
							}
							const globalVariableContext = GetContextualAutoCompleteByGlobalVariable(currentSen, start);
							// let NormalProvider = new ItemProvider([],globalVariableContext);
							// context.subscriptions.pop()
							// let solnorPv = vscode.languages.registerCompletionItemProvider("solidity", NormalProvider,'.');  
							// context.subscriptions.push(solnorPv);
							demoProvider.Items = globalVariableContext;
							demoProvider.codeComs = [];
						}
					}
				}
			}
		})
	}
	// let serverModule = context.asAbsolutePath(
    //     path.join('out', 'server.js')
    // );

    // let serverOptions: ServerOptions = {
    //     module: serverModule, transport: TransportKind.ipc
    // };
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

async function recommendToken(curLen : number, currentSen : any, curContext : string) {
	const uri = '49.235.239.68:9065/tokenPredict'
        // set two minutes as a limit duration of testing
        let strjson = JSON.stringify({
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
export function deactivate() {
	// if (!client) {
    //     return undefined;
    // }
    // return client.stop();
}
