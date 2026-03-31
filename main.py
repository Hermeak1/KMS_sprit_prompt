import crawler
import NPC_manager


def run():
    try:
        collection = crawler.setup_collection()
        NPC_manager.init(collection)
        print("준비 완료! ('종료' 입력 시 종료)\n")
    except Exception as e:
        print(f"초기화 오류: {e}")
        return

    while True:
        user_input = input("용사: ")
        if user_input.lower() in ("exit", "quit", "종료"):
            break
        try:
            response = NPC_manager.chat(user_input)
            print(f"정령: {response}\n")
        except Exception as e:
            print(f"NPC 응답 오류: {e}")


run()
