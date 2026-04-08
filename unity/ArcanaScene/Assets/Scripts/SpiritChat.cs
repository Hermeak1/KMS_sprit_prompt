using System.Collections;
using UnityEngine;
using UnityEngine.Networking;
using TMPro;

[System.Serializable]
public class ChatRequest
{
    public string message;
    public string session_id = "player_1";
}

[System.Serializable]
public class ChatResponse
{
    public string reply;
    public int prompt_tokens;
    public int completion_tokens;
    public int total_tokens;
}

public class SpiritChat : MonoBehaviour
{
    [Header("서버 설정")]
    public string serverUrl = "http://127.0.0.1:8080/chat";

    [Header("UI 연결")]
    public TMP_Text bubbleText;
    public GameObject speechBubble;
    public TMP_InputField inputField;
    public TMP_Text tokenInfoText;

    [Header("플레이어 말풍선")]
    public TMP_Text playerBubbleText;
    public GameObject playerSpeechBubble;

    [Header("애니메이션")]
    public Transform spiritImage;

    private bool isWaiting = false;
    private Vector3 _spiritOriginPos;

    private void Start()
    {
        inputField.onSubmit.AddListener(_ => OnSendClicked());
        if (spiritImage != null)
            _spiritOriginPos = spiritImage.localPosition;

        // Inspector 연결 실패 시 자동 탐색 (transform.Find는 비활성 오브젝트도 탐색 가능)
        if (playerSpeechBubble == null)
        {
            Transform found = transform.Find("PlayerSpeechBubble");
            if (found != null) playerSpeechBubble = found.gameObject;
        }

        if (playerBubbleText == null && playerSpeechBubble != null)
            playerBubbleText = playerSpeechBubble.GetComponentInChildren<TMP_Text>(true);

       // Debug.Log($"[Start] playerSpeechBubble={playerSpeechBubble?.name}, playerBubbleText={playerBubbleText?.name}");
    }

    public void OnSendClicked()
    {
        if (isWaiting || string.IsNullOrWhiteSpace(inputField.text)) return;
        StartCoroutine(SendChatMessage(inputField.text));
        inputField.text = "";
        inputField.ActivateInputField();
    }

    private IEnumerator SendChatMessage(string userMessage)
    {
        isWaiting = true;
        speechBubble.SetActive(false);

        // 플레이어 말풍선 표시 -> test시 디버깅 블럭 활성/비활성
     //   Debug.Log($"[Player Bubble] bubble={playerSpeechBubble}, text={playerBubbleText}");
        if (playerSpeechBubble != null && playerBubbleText != null)
        {
            playerBubbleText.text = userMessage;
            ResizeBubble(playerSpeechBubble, playerBubbleText);
            playerSpeechBubble.SetActive(true);
      //      Debug.Log($"[Player Bubble] 활성화 완료: {userMessage}");
        }

        // 대기 중 애니메이션 
        Coroutine bounceCoroutine = null;
        if (spiritImage != null)
            bounceCoroutine = StartCoroutine(BounceLoop());

        var request = new ChatRequest { message = userMessage };
        string json = JsonUtility.ToJson(request);
        byte[] body = System.Text.Encoding.UTF8.GetBytes(json);

        using var www = new UnityWebRequest(serverUrl, "POST");
        www.uploadHandler   = new UploadHandlerRaw(body);
        www.downloadHandler = new DownloadHandlerBuffer();
        www.SetRequestHeader("Content-Type", "application/json");

        yield return www.SendWebRequest();

        // 애니메이션 종료 후 원래 위치로
        if (bounceCoroutine != null)
        {
            StopCoroutine(bounceCoroutine);
            spiritImage.localPosition = _spiritOriginPos;
        }

        if (www.result == UnityWebRequest.Result.Success)
        {
            var res = JsonUtility.FromJson<ChatResponse>(www.downloadHandler.text);
            bubbleText.text = res.reply;
            ResizeBubble(speechBubble, bubbleText);
            speechBubble.SetActive(true);

            if (tokenInfoText != null)
                tokenInfoText.text = $"입력 {res.prompt_tokens} / 출력 {res.completion_tokens} / 합계 {res.total_tokens}";
        }
        else
        {
            bubbleText.text = "잠깐, 잘 못 들었담. 다시 말해달람.";
            ResizeBubble(speechBubble, bubbleText);
            speechBubble.SetActive(true);
            Debug.LogError($"[SpiritChat] 오류: {www.error}");
        }

        isWaiting = false;
    }

    private void ResizeBubble(GameObject bubble, TMP_Text text)
    {
        text.ForceMeshUpdate();
        RectTransform rect = bubble.GetComponent<RectTransform>();
        float padding = 30f;
        rect.sizeDelta = new Vector2(rect.sizeDelta.x, text.preferredHeight + padding);
    }

    private IEnumerator BounceLoop()
    {
        float bounceHeight = 18f;
        float bounceSpeed  = 3.5f;
        float t = 0f;

        while (true)
        {
            t += Time.deltaTime * bounceSpeed;
            float offsetY = Mathf.Abs(Mathf.Sin(t)) * bounceHeight;
            spiritImage.localPosition = _spiritOriginPos + new Vector3(0f, offsetY, 0f);
            yield return null;
        }
    }
}
