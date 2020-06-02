import * as vscode from 'vscode';

let urllib:any = require('urllib-sync');

export class ItemProvider implements vscode.CompletionItemProvider{
	public codeComs : string[];
	public Items : vscode.CompletionItem[];

	constructor(codeComs : string[], Items : vscode.CompletionItem[]){
		this.codeComs = codeComs;
		this.Items = Items;
	};

	public sendRequest(url: string, data: string) {
		let options = {
			method: 'POST',
			headers:{"content-type": "application/json"},
			content: data,
			timeout: 60000
		};
		let rebody = urllib.request(url, options).data;
		// console.log('rebody:' + rebody);
		var asciis = rebody;
		var resString = "";
	
		for(var asc of asciis) {
			resString += String.fromCharCode(asc);
		}
	
		rebody = JSON.parse(resString);
		return rebody;
	}
	
    public provideCompletionItems(document: vscode.TextDocument, position: vscode.Position, token: vscode.CancellationToken, context: vscode.CompletionContext): vscode.CompletionItem[]{	

		if (context.triggerCharacter === ' ' || context.triggerCharacter === '\n') {  // token suggestion
			var previous = document.getText(new vscode.Range(new vscode.Position(0,0), position));
			var sentence = document.lineAt(position).text;
			var curLine = position.line;
			// console.log("Context:", previous);
			// console.log("Sentence:", sentence);
			// console.log("CurLine:", curLine);

			var jsonObj = {"sentence":(sentence), "context":(previous), "curLine":(curLine)};
			var strjson = JSON.stringify(jsonObj);

			const senUrl = "http://49.235.239.68:9065/tokenPredict";
			var res = this.sendRequest(senUrl, strjson);

			var CList = new Array();
			var arr = res.data.results;

			// display candidates in probablidity order
			for(var i in arr) {
				var temp = new vscode.CompletionItem(arr[i], vscode.CompletionItemKind.Field);
				if (i.length === 1) 
					temp.sortText = '0' + i;
				else 
					temp.sortText = i;
				CList.push(temp);
			}

			// superagent.post(senUrl)
			// 	.send(strjson)
			// 	.end((err: Error, res: superagent.Response) => {
			// 		if (!err) {
			// 			var arr = JSON.parse(res.text).data.results;
			// 			for(var it in arr) {
			// 				var temp = new vscode.CompletionItem(it, vscode.CompletionItemKind.Field);
			// 				temp.sortText = cnt.toString();
			// 				CList.push(temp);
			// 				cnt += 1;
			// 			}

			// 		} else{
			// 			console.log('err:' + err);
			// 		}
			// 	});
			// this.codeComs = CList;
			return CList;
		}
		else if (context.triggerCharacter === '.') {  // API completion
			// console.log("Items *", (this.Items).length, this.Items);
			return this.Items;
		}
		else {  // current word completion
			return [];
		}
	}
	
    public resolveCompletionItem(item: vscode.CompletionItem, token: vscode.CancellationToken): any{
        return null;
	}
	
    dispose(){

    }
}