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
		console.log("token:", token);
		if (context.triggerCharacter === ' ') {  // token suggestion
			var previous = document.getText(new vscode.Range(new vscode.Position(0,0), position));
			// console.log(previous, "**");
			var cnt = 1;
			var jsonObj = {"context":(previous)};
			var strjson = JSON.stringify(jsonObj);

			const senUrl = "http://49.235.239.68:9065/tokenPredict";
			var res = this.sendRequest(senUrl, strjson);

			var CList = new Array();
			var arr = res.data.results;
			for(var it of arr) {
				var temp = new vscode.CompletionItem(it, vscode.CompletionItemKind.Field);
				temp.sortText = cnt.toString();
				CList.push(temp);
				cnt += 1;
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
			this.codeComs = CList;
			return CList;
		}
		else if (context.triggerCharacter === '.') {  // API completion
			console.log("Items *", (this.Items).length, this.Items);
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