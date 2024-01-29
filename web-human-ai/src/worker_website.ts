import { log_data, get_json, get_html } from "./connector";
import { DEVMODE } from "./globals";
import { timer, range } from "./utils";

let main_text_area = $("#main_text_area")

export async function setup_intro_information_1() {
    // hide for now
    $("#short_instructions").toggle(false)
    main_text_area.html(await get_html("instructions_1.html"))
    await timer(10)
    $("#button_next").on("click", setup_intro_information_2)
}

export async function setup_intro_information_2() {
    main_text_area.html(await get_html("instructions_2.html"))
    await timer(10)
    $("#button_next").on("click", setup_intro_information_3)
}

export async function setup_intro_information_3() {
    main_text_area.html(await get_html("instructions_3.html"))
    await timer(10)
    $("#button_next").on("click", setup_intro_information_4)
}

export async function setup_intro_information_4() {
    // show short instructions
    $("#short_instructions").toggle(true)
    main_text_area.html(await get_html("instructions_4.html"))
    await timer(10)
    $("#button_next").on("click", setup_main_question)
}

function next_main_question() {
    globalThis.data_i += 1;
    if (globalThis.data_i >= globalThis.data.length) {
        load_thankyou()
    } else {
        globalThis.data_now = globalThis.data[globalThis.data_i]
        setup_main_question()
    }
}


export async function setup_main_question() {
    globalThis.time_start = Date.now()


    let html = await get_html("main_task.html")
    html = html.replace("{{SRC}}", globalThis.data_now["src"])
    html = html.replace("{{TGT}}", globalThis.data_now["tgt"])
    html = html.replaceAll("{{AI_PREDICTION_VALUE}}", globalThis.data_now["ai"]["overall"])

    main_text_area.html(html)
    await timer(10)

    let human_answer_val = null 
    $("#human_answer_val").on("input", (x) => {
        let el = $(x.target)
        human_answer_val = el.val()
        $("#human_answer_label").text(human_answer_val as string)
    })

    $("#button_submit").on("click", () => {
        next_main_question()
        log_data(human_answer_val)
    })
}

async function load_thankyou() {
    main_text_area.html("Please wait 3s for data synchronization to finish.")
    await timer(1000)
    main_text_area.html("Please wait 2s for data synchronization to finish.")
    await timer(1000)
    main_text_area.html("Please wait 1s for data synchronization to finish.")
    await timer(1000)

    let html_text = `Thank you for participating in our study. For any further questions about this project or your data, <a href="mailto:vilem.zouhar@inf.ethz.ch">send us a message</a>.`;
    console.log("PID", globalThis.prolific_pid)
    if (globalThis.prolific_pid != null) {
        html_text += `<br>Please click <a class="button_like" href="https://app.prolific.com/submissions/complete?cc=C6XCI3SV">this link</a> to go back to Prolific. `
        html_text += `Alternatively use this code <em>C6XCI3SV</em>.`
    }
    main_text_area.html(html_text);
}