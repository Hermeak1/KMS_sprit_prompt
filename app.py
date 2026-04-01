import gradio as gr
import crawler
import NPC_manager

# ── 초기화 ────────────────────────────────────────
print("아르카나 데이터 수집 중...")
collection = crawler.setup_collection()
NPC_manager.init(collection)
print("준비 완료!")


# ── 응답 함수 ─────────────────────────────────────
def respond(user_message, history):
    # Gradio 최신 버전: history는 {"role": ..., "content": ...} 딕셔너리 리스트
    openai_history = [msg for msg in history]

    NPC_manager.history = openai_history
    reply, usage = NPC_manager.chat(user_message)

    history.append({"role": "user",      "content": user_message})
    history.append({"role": "assistant", "content": reply})

    token_info = (
        f"📨 요청(입력): {usage['prompt_tokens']} 토큰  |  "
        f"💬 응답(출력): {usage['completion_tokens']} 토큰  |  "
        f"🔢 총 사용: {usage['total_tokens']} 토큰"
    )
    return history, token_info


# ── UI ────────────────────────────────────────────
css = """
.avatar-container { width: 100px !important; height: 100px !important; }
.avatar-container img { width: 100px !important; height: 100px !important; min-width: 100px !important; min-height: 100px !important; }
#chatbot { resize: vertical !important; overflow: auto !important; min-height: 300px !important; }
"""

scroll_js = """
() => {
    const targets = document.querySelectorAll('#chatbot *');
    for (const el of targets) {
        if (el.scrollHeight > el.clientHeight) {
            el.scrollTop = el.scrollHeight;
        }
    }
}
"""

with gr.Blocks(title="🌿 아르카나 돌의 정령") as demo:
    gr.Markdown("<h1 style='text-align:center'>🌿 아르카나 돌의 정령</h1><p style='text-align:center'>메이플스토리 아르카나 숲의 돌의 정령과 대화해보세요!</p>")

    chatbot = gr.Chatbot(
        height=500,
        avatar_images=(None, "spirit.png"),
        autoscroll=True,
        elem_id="chatbot"
    )
    token_display = gr.Textbox(
        label="토큰 사용량",
        interactive=False,
        value="아직 대화가 없담..."
    )

    with gr.Row():
        msg = gr.Textbox(placeholder="용사님, 말을 걸어달람~", scale=5, show_label=False)
        send_btn = gr.Button("전송", scale=1)

    clear_btn = gr.Button("대화 초기화")

    send_btn.click(respond, [msg, chatbot], [chatbot, token_display]).then(
        lambda: "", outputs=msg
    ).then(fn=None, js=scroll_js)

    msg.submit(respond, [msg, chatbot], [chatbot, token_display]).then(
        lambda: "", outputs=msg
    ).then(fn=None, js=scroll_js)

    clear_btn.click(
        lambda: ([], "아직 대화가 없담..."),
        outputs=[chatbot, token_display]
    )

demo.launch(css=css)
