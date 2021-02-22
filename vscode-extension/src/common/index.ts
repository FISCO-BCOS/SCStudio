import axios from "axios";
import * as vscode from "vscode";

export async function postRequest<Response>(
    request: string,
    serverAddress: string,
    data: Object,
    retryCount: number = 3
) {
    while (true) {
        try {
            let response: Response = await axios
                .post(`http://${serverAddress}/${request}`, data)
                .then((response) => {
                    if (response.status !== 200) {
                        throw new Error(response.statusText);
                    }
                    return response.data;
                });
            return response;
        } catch (error) {
            retryCount -= 1;
            if (retryCount === 0) {
                throw new Error(error.code);
            }
        }
    }
}
