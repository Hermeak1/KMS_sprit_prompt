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

    private bool isWaiting = false;

    private void Start()
    {
        inputField.onSubmit.AddListener(_ => OnSendClicked());
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

        var request = new ChatRequest { message = userMessage };
        string json = JsonUtility.ToJson(request);
        byte[] body = System.Text.Encoding.UTF8.GetBytes(json);

        using var www = new UnityWebRequest(serverUrl, "POST");
        www.uploadHandler   = new UploadHandlerRaw(body);
        www.downloadHandler = new DownloadHandlerBuffer();
        www.SetRequestHeader("Content-Type", "application/json");

        yield return www.SendWebRequest();

        if (www.result == UnityWebRequest.Result.Success)
        {
            var res = JsonUtility.FromJson<ChatResponse>(www.downloadHandler.text);
            bubbleText.text = res.reply;
            speechBubble.SetActive(true);

            if (tokenInfoText != null)
                tokenInfoText.text = $"입력 {res.prompt_tokens} / 출력 {res.completion_tokens} / 합계 {res.total_tokens}";
        }
        else
        {
            bubbleText.text = "잠깐, 잘 못 들었담. 다시 말해달람.";
            speechBubble.SetActive(true);
            Debug.LogError($"[SpiritChat] 오류: {www.error}");
        }

        isWaiting = false;
    }
}
