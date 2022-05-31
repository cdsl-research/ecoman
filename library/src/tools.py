import requests
import json


def slack_notify(message: str, slack_webhook: str):
    """Slack通知"""

    assert len(slack_webhook) > 20, "Invalid slack_webhook"
    try:
        requests.post(
            slack_webhook,
            data=json.dumps(
                {
                    "text": message,  # 投稿するテキスト
                }
            ),
        )
    except Exception as e:
        print("Fail to send a message to slack:", e)
