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
with gr.Blocks(title="🌿 아르카나 돌의 정령") as demo:
    gr.Markdown("# 🌿 아르카나 돌의 정령\n메이플스토리 아르카나 숲의 돌의 정령과 대화해보세요!")

    chatbot = gr.Chatbot(height=500)
    token_display = gr.Textbox(
        label="토큰 사용량",
        interactive=False,
        value="아직 대화가 없담..."
    )

    with gr.Row():
        msg = gr.Textbox(placeholder="용사님, 말을 걸어달람~", scale=9, show_label=False)
        send_btn = gr.Button("전송", scale=1)

    clear_btn = gr.Button("대화 초기화")

    send_btn.click(respond, [msg, chatbot], [chatbot, token_display]).then(
        lambda: "", outputs=msg
    )
    msg.submit(respond, [msg, chatbot], [chatbot, token_display]).then(
        lambda: "", outputs=msg
    )
    clear_btn.click(
        lambda: ([], "아직 대화가 없담..."),
        outputs=[chatbot, token_display]
    )
    

demo.launch()
