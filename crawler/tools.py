def slack_notify(message):
    """ Slack通知 """
    import requests
    import os
    SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK')
    if SLACK_WEBHOOK:
        requests.post(SLACK_WEBHOOK, data=json.dumps({
            'text': message,  # 投稿するテキスト
        }))
