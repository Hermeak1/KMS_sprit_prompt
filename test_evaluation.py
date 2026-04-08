"""
돌의 정령 챗봇 정량 평가 스크립트
- 말투 유지율: 담/람 어미 유지 비율, 금지 어미 이탈 비율
- 모델 비교: gpt-5.4-nano vs gpt-5.4-mini (응답 시간, 토큰 비용, 말투 유지율)
"""

import time
import re
import NPC_manager
import crawler

# ── 테스트 질문 세트 ──────────────────────────────────────────────
TEST_QUESTIONS = [
    "안녕",
    "넌 누구야?",
    "여기가 어디야?",
    "탈라하트 알아?",
    "무서워?",
    "나 도와줄 수 있어?",
    "기분이 어때?",
    "아르카나가 뭐야?",
    "같이 가줄 수 있어?",
    "고마워",
    "뭐가 좋아?",
    "힘들어?",
    "나한테 화났어?",
    "여기서 뭐하고 있어?",
    "친구 있어?",
    "슬프지 않아?",
    "용사님이 뭐야?",
    "위험해?",
    "잘 있었어?",
    "뭐 도와줄까?",
]

FORBIDDEN = re.compile(r'(되담|오르담|좋아담|큰담|좋달람|있달람|할게달람|게담|알아담|도와주담|정말이람|정말이담|그래담)')
SPIRIT_ENDING = re.compile(r'[담람]')

TEST_QUESTIONS = TEST_QUESTIONS[:5]  # 빠른 테스트용 (전체 실행 시 이 줄 제거)

MODELS = ["gpt-5.4-nano", "gpt-5.4-mini"]


# ── 단일 모델 평가 ────────────────────────────────────────────────
def evaluate_model(model_name: str, collection) -> dict:
    print(f"\n{'='*55}")
    print(f"  모델: {model_name}")
    print(f"{'='*55}")

    # NPC_manager의 모델을 동적으로 교체
    import NPC_manager as nm
    original_call = nm._call_api

    def patched_call(system_prompt, recent_history, user_message):
        return nm.client.chat.completions.create(
            model=model_name,
            messages=[system_prompt] + recent_history,
            max_completion_tokens=300
        )

    nm._call_api = patched_call
    nm.history.clear()
    nm.init(collection)

    results = []

    for i, q in enumerate(TEST_QUESTIONS, 1):
        nm.history.clear()  # 각 질문을 독립 평가 (히스토리 누적 방지)
        start = time.time()
        try:
            reply, usage = nm.chat(q)
            elapsed = time.time() - start

            has_ending   = bool(SPIRIT_ENDING.search(reply))
            has_forbidden = bool(FORBIDDEN.search(reply))

            results.append({
                "question":      q,
                "reply":         reply,
                "elapsed":       elapsed,
                "prompt_tokens": usage["prompt_tokens"],
                "comp_tokens":   usage["completion_tokens"],
                "total_tokens":  usage["total_tokens"],
                "has_ending":    has_ending,
                "has_forbidden": has_forbidden,
                "pass":          has_ending and not has_forbidden,
            })

            status = "pass" if results[-1]["pass"] else ("금지어미" if has_forbidden else "어미없음")
            print(f"  [{i:02d}] {status}  {q!r:20s} → {reply[:40]}")

        except Exception as e:
            elapsed = time.time() - start
            results.append({
                "question": q, "reply": f"ERROR: {e}",
                "elapsed": elapsed, "prompt_tokens": 0,
                "comp_tokens": 0, "total_tokens": 0,
                "has_ending": False, "has_forbidden": False, "pass": False,
            })
            print(f"  [{i:02d}] !! ERROR !! {q!r} → {e}")

    nm._call_api = original_call  # 원복
    return _summarize(model_name, results)


# ── 결과 요약 ─────────────────────────────────────────────────────
def _summarize(model_name: str, results: list) -> dict:
    n = len(results)
    passed       = sum(1 for r in results if r["pass"])
    forbidden    = sum(1 for r in results if r["has_forbidden"])
    no_ending    = sum(1 for r in results if not r["has_ending"])
    avg_time     = sum(r["elapsed"] for r in results) / n
    avg_prompt   = sum(r["prompt_tokens"] for r in results) / n
    avg_comp     = sum(r["comp_tokens"] for r in results) / n
    avg_total    = sum(r["total_tokens"] for r in results) / n

    return {
        "model":          model_name,
        "total":          n,
        "passed":         passed,
        "pass_rate":      passed / n * 100,
        "forbidden_cnt":  forbidden,
        "no_ending_cnt":  no_ending,
        "avg_time_s":     avg_time,
        "avg_prompt_tok": avg_prompt,
        "avg_comp_tok":   avg_comp,
        "avg_total_tok":  avg_total,
        "detail":         results,
    }


# ── 최종 비교표 출력 ──────────────────────────────────────────────
def print_comparison(summaries: list[dict]):
    print(f"\n\n{'='*65}")
    print(" **** 모델 비교 결과")
    print(f"{'='*65}")
    header = f"{'모델':<18} {'말투유지율':>8} {'금지어미':>8} {'어미없음':>8} {'평균시간':>9} {'평균토큰':>9}"
    print(header)
    print("-" * 65)
    for s in summaries:
        print(
            f"  {s['model']:<16} "
            f"{s['pass_rate']:>7.1f}%  "
            f"{s['forbidden_cnt']:>7}건  "
            f"{s['no_ending_cnt']:>7}건  "
            f"{s['avg_time_s']:>7.2f}s  "
            f"{s['avg_total_tok']:>7.0f}tok"
        )
    print(f"{'='*65}")

    # 토큰 비용 추정 (OpenAI 공식 가격 기준)
    PRICE = {
        "gpt-5.4-nano": {"in": 0.20, "out": 1.25},
        "gpt-5.4-mini": {"in": 0.75, "out": 4.50},
    }
    print("\n 예상 비용 (질문 1,000회 기준, USD)")
    print(f"  {'모델':<18} {'입력비용':>10} {'출력비용':>10} {'합계':>10}")
    print("  " + "-" * 52)
    for s in summaries:
        p = PRICE.get(s["model"], {"in": 0, "out": 0})
        cost_in  = s["avg_prompt_tok"] * 1000 / 1_000_000 * p["in"]
        cost_out = s["avg_comp_tok"]   * 1000 / 1_000_000 * p["out"]
        print(f"  {s['model']:<18} ${cost_in:>9.4f}  ${cost_out:>9.4f}  ${cost_in+cost_out:>9.4f}")
    print()


# ── 메인 ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("ChromaDB 초기화 중...")
    collection = crawler.setup_collection()

    summaries = []
    for model in MODELS:
        s = evaluate_model(model, collection)
        summaries.append(s)

    print_comparison(summaries)

    # 상세 응답 로그 저장
    import json, datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = f"eval_result_{timestamp}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(summaries, f, ensure_ascii=False, indent=2,
                  default=lambda o: str(o))
    print(f"  상세 로그 저장 완료: {log_path}")
