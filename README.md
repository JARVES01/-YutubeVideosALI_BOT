# YutubeVideosALI_BOT

Telegram bot that downloads YouTube videos and audio (mp3) with language selection (UZ / RU / EN).

## How to use

1. Create a Telegram bot via BotFather and get the token.
2. Set the environment variable `BOT_TOKEN` on your hosting platform (or edit `main.py` to insert your token).
3. Deploy on Render / Railway / any Python host. Example start command:
```
python main.py
```

## Files
- `main.py` - bot code
- `requirements.txt` - Python dependencies
- `.gitignore` - ignores temp and media files

## Notes
- Telegram has file size limits; large videos may not be deliverable via Telegram directly.
- For production use, consider adding size checks, queues, and storage (S3) for large files.
