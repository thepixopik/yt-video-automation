# yt-video-automation

Automated **2D Flat-Vector Documentary Video Factory** (`PyCairo` + `FFmpeg` + `GitHub Actions` → **Cloudflare R2**).

Whenever you push a new folder under `videos/<slug>/` (containing `render.py` and optionally `voiceover.wav` or `voiceover.mp3`), GitHub Actions automatically:
1. Renders the **1080×1920 @ 30 fps** procedural 2D vector animation with `PyCairo`.
2. Mixes procedural UI/foley SFX with your voiceover audio using `FFmpeg`.
3. Uploads the finished MP4 directly to your Cloudflare R2 bucket **`gemini-media-vault`**.
4. Publishes the live public URL in the Actions Job Summary:
   `https://pub-e6c09b30e18c436c9dd94c55aa2aedd5.r2.dev/<slug>.mp4`

## One-Time Setup (GitHub Secrets)

Go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret Name | Value |
|---|---|
| `CLOUDFLARE_ACCOUNT_ID` | `88f57683348cf1c6f66c6b52553452a2` |
| `CLOUDFLARE_API_TOKEN` | Cloudflare API Token with **Workers R2 Storage: Edit** permission |
