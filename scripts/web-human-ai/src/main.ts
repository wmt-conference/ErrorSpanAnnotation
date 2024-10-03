import { DEVMODE } from "./globals"
export var UID: string
import { load_data } from './connector'
import { setup_intro_information_1, setup_main_question } from "./worker_website"

globalThis.data = null
globalThis.reward = 0

const urlParams = new URLSearchParams(window.location.search);
globalThis.uid = urlParams.get('uid')
globalThis.data_i = Number.parseInt(urlParams.get('data_i')) || 0
globalThis.skip_intro = urlParams.has('skip_intro')

async function get_uid_and_data() {
    // set to "demo" uid if in devmode and uid doesn't exist
    if (DEVMODE && globalThis.uid == null) {
        document.location.href = document.location.href += "?uid=demo";
    }

    globalThis.prolific_pid = urlParams.get('prolific_pid');
    globalThis.session_id = urlParams.get('session_id');
    globalThis.study_id = urlParams.get('study_id');

    // repeat until we're able to load the data
    while (globalThis.data == null) {
        if (globalThis.uid == null) {
            let UID_maybe = null
            while (UID_maybe == null) {
                UID_maybe = prompt("What is your user id?")
            }
            globalThis.uid = UID_maybe!;
        }

        await load_data().then((data: any) => {
            globalThis.data = data
            globalThis.data_now = globalThis.data[globalThis.data_i];
            if (globalThis.skip_intro) {
                setup_main_question()
            } else {
                setup_intro_information_1()
            }
        }).catch((reason: any) => {
            console.error(reason)
            alert("Invalid UID " + globalThis.uid);
            globalThis.uid = null;
        });
    }

}

get_uid_and_data()