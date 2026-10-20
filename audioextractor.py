
import re
import shutil
import tempfile
from pathlib import Path

import streamlit as st
import yt_dlp

st.set_page_config(
    page_title="Audio Extractor",
    page_icon="🎧",
    layout="centered",
)

st.markdown("""
<style>
.stApp {
    background: #0B1220;
    color: #F8FAFC;
}
.block-container {
    max-width: 700px;
    padding-top: 3rem;
}
h1, h2, h3, p, label {
    color: #F8FAFC !important;
}
.subtitle {
    color: #94A3B8 !important;
}
.stTextInput input, .stSelectbox div[data-baseweb="select"] {
    background: #111C2E;
    color: #F8FAFC;
}
.stButton > button {
    background: #22D3EE;
    color: #0B1220;
    border: none;
    border-radius: 10px;
    font-weight: 700;
    width: 100%;
    min-height: 3rem;
}
.stDownloadButton > button {
    background: #34D399;
    color: #0B1220;
    border: none;
    border-radius: 10px;
    font-weight: 700;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

st.title("🎧 Audio Extractor")
st.markdown(
    '<p class="subtitle">Extract the sound. Keep the music.</p>',
    unsafe_allow_html=True,
)

st.write("### Paste your YouTube link")
st.caption("Convert a publicly accessible YouTube video into an MP3 audio file.")

url = st.text_input(
    "YouTube URL",
    placeholder="https://www.youtube.com/watch?v=...",
)

quality = st.selectbox(
    "Audio quality",
    ["128K", "192K", "256K", "320K"],
    index=1,
)

def valid_youtube_url(value):
    try:
        from urllib.parse import urlparse

        parsed = urlparse(value.strip())
        host = (parsed.hostname or "").lower()

        allowed = {
            "youtube.com",
            "www.youtube.com",
            "m.youtube.com",
            "music.youtube.com",
            "youtu.be",
            "www.youtu.be",
        }

        return host in allowed and parsed.scheme in ("http", "https")
    except Exception:
        return False


if st.button("Extract Audio"):
    if not url.strip():
        st.warning("Please paste a YouTube link first.")

    elif not valid_youtube_url(url):
        st.warning("Please enter a valid YouTube video URL.")

    elif not shutil.which("ffmpeg"):
        st.error("Audio conversion is unavailable because FFmpeg is missing.")
        st.info("Check the Streamlit Cloud app logs and dependency installation.")

    else:
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                output_template = str(Path(temp_dir) / "audio.%(ext)s")

                options = {
                    "format": "bestaudio/best",
                    "outtmpl": output_template,
                    "noplaylist": True,
                    "quiet": True,
                    "no_warnings": True,
                    "retries": 3,
                    "socket_timeout": 30,
                    "ffmpeg_location": shutil.which("ffmpeg"),
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": quality.replace("K", ""),
                        }
                    ],
                }

                progress = st.progress(0)
                status = st.empty()

                with yt_dlp.YoutubeDL(options) as downloader:
                    status.info("Fetching video audio...")
                    downloader.download([url.strip()])

                mp3_path = Path(temp_dir) / "audio.mp3"

                if not mp3_path.exists() or mp3_path.stat().st_size == 0:
                    st.error("The MP3 file could not be created.")
                else:
                    audio_bytes = mp3_path.read_bytes()
                    progress.progress(100)
                    status.success("Your audio is ready!")

                    st.audio(audio_bytes, format="audio/mpeg")

                    st.download_button(
                        label="⬇ Download MP3",
                        data=audio_bytes,
                        file_name="extracted_audio.mp3",
                        mime="audio/mpeg",
                    )

        except Exception:
            st.error(
                "YouTube could not provide this audio right now. "
                "The video may be restricted or YouTube may require "
                "additional verification."
            )
