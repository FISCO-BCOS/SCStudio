import superagent = require('superagent');

export async function postRequest(url: string, data: object) {
    const promise = new Promise<superagent.Response>((resolve, reject) => {
        superagent.post(url)
            .send(data)
            .end((err: Error, res: superagent.Response) => {
                if (!err) {
                    resolve(res);
                } else{
                    console.log('err:' + err);
                    reject(err);
                }
            });
    });
    return promise;
}

export async function postStringRequest(url: string, data: string) {
    const promise = new Promise<superagent.Response>((resolve, reject) => {
        superagent.post(url)
            .send(data)
            .end((err: Error, res: superagent.Response) => {
                if (!err) {
                    resolve(res);
                } else{
                    console.log('err:' + err);
                    reject(err);
                }
            });
    });
    return promise;
}

export async function getRequest(url: string) {
    const promise = new Promise<superagent.Response>(function (resolve, reject) {
        superagent.get(url)
            .end(function (err, res) {
                if (!err) {
                    resolve(res);
                } else {
                    console.log(err);
                    reject(err);
                }
            });
    });
    return promise;
}