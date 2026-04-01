# 🍁 돌의 정령 챗봇

![Python](https://img.shields.io/badge/Python-3.11-blue)
![OpenAI](https://img.shields.io/badge/GPT-5.4--mini-green)
![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-orange)

메이플스토리를 어릴 때부터 해왔는데, 아르카나 돌의 정령 말투가 너무 특이해서 LLM으로 구현해보고 싶었음. 프롬프트만 짜면 세계관을 몰라서 엉뚱한 소리를 하기 때문에 RAG로 아르카나 데이터를 직접 구축해서 제작.

```
용사: 아르카나 숲에는 어떤 정령들이 살아?
정령: 나무정령, 물정령, 바람정령이 내 친구들담! 다들 숲을 지키고 있담.
      무서운 일이 생기면 같이 도와주는 든든한 친구들담~
```

---

## 쓴 것들

| | |
|---|---|
| LLM | GPT-5.4-mini |
| Vector DB | ChromaDB |
| Embedding | text-embedding-3-small |
| 크롤링 | BeautifulSoup4 |
| UI | Streamlit |

---

## 실행 방법

```bash
python -m venv maple-spirit
source maple-spirit/bin/activate  # Windows: maple-spirit\Scripts\activate
pip install -r requirements.txt
```

`.env` 파일 만들고 API 키 넣기

```
OPENAI_API_KEY=your_api_key_here
```

```bash
python crawl.py       # 데이터 수집
python vectordb.py    # DB 저장
python chat.py        # 실행 (터미널)
streamlit run app.py  # UI 버전
```

---

## 파일 구조

```
maple-spirit/
├── crawl.py
├── vectordb.py
├── chat.py
├── app.py
├── requirements.txt
└── README.md
```

---

## 만들면서 고민한 것들

**RAG 없이 선 테스트**

GPT한테 "돌의 정령처럼 말해줘" 하면 세계관 기반 질문에서 틀린 답 내거나 "잘 모르겠어요" 하는 경우가 꽤 있었기 때문에, 나무위키에서 아르카나 스토리 데이터 크롤링해서 ChromaDB에 넣고 나서는 퀘스트 관련 질문도 제대로 답하기 시작.

**모델 nano VS mini 선택**

처음엔 gpt-5.4-nano로 테스트했는데 말투 규칙을 상기시키지 않으면 룰 적용이 미흡함. "좋달람" 같은 잘못된 어미가 나오거나 그냥 평범한 문체로 돌아오는 경우가 있음. mini로 변경 후 안정적으로 룰 적용이 되어 mini로 결정. 단, 비용 차이가 있는 편.

**말투 잡는 게 생각보다 오래 걸림**

처음엔 "~달람, ~담 어미 써줘" 정도만 프롬프트에 넣었지만 "정령들이담" 같은 어색한 표현이 지속적으로 도출. 나쁜 예 / 좋은 예 형식으로 few-shot 넣고 나서야 안정되었음.

개선 과정 요약:
```
v1. 페르소나 + 기본 어미 규칙만
    → "좋달람", "있달람" 같은 잘못된 어미 지속 발생

v2. few-shot 예시 추가
    → 많이 나아졌지만 "~이담" 처리가 아직 어색함

v3. "~이다 → ~담" 규칙 명시 + 프롬프트 압축
    → 안정적으로 유지

v4. 동사/형용사/기타 어미 변환 규칙 분리 명시 + 금지 패턴 목록 추가
    → "되담", "오르담", "좋아담" 같은 잘못된 변환 차단
    → 문장 전체를 먼저 자연스럽게 만든 뒤 마지막 어미만 바꾸도록 순서 명시
```

**토큰 절약**

컨텍스트가 매 요청마다 통째로 들어가는 구조라서 관리하지 않으면 비용이 생각보다 빠르게 나옴. 아래 방법으로 40~50% 정도 절감.

- 시스템 프롬프트 압축 (규칙만 남기고 나머지 제거)
- n_results 3 → 2
- context 글자 수 500자로 제한 (`MAX_CONTEXT_CHARS`)
- 대화 기록 최근 2턴만 유지 (`MAX_HISTORY_TURNS`)
- max_completion_tokens=300 제한

**UI 개선**

- 대화마다 스크롤 자동 추적 적용
- 사용자가 창 크기를 직접 조절할 수 있도록 변경

---

## 아쉬운 점

크롤링 데이터가 적어서 사냥터 추천, 스펙 관련 질문은 제대로 답변이 안 됨. 게임 메타 정보는 별도로 데이터를 구축해야 할 것으로 보임.

---

## 추후 개선 방향

- Unity C#에서 API 직접 호출해서 실제 게임 내 NPC 형태로 연동 (기존 Unity 개발 경험 활용)
- 친밀도 상태 변수 추가해서 대화 횟수에 따라 반응이 달라지는 구조 구현
- 다른 아르카나 정령 캐릭터 추가
