
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st
import yt_dlp

st.set_page_config(
    page_title="Audio Extractor",
    page_icon="🎧",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Color palette
MIDNIGHT_NAVY = "#0B1220"
DEEP_NAVY = "#111C2E"
SLATE_BLUE = "#1E293B"
ELECTRIC_CYAN = "#22D3EE"
ICE_WHITE = "#F8FAFC"
STEEL_GRAY = "#94A3B8"
BORDER_BLUE = "#334155"

# Custom styling
st.markdown(f"""
<style>
.stApp {{
    background-color: {MIDNIGHT_NAVY};
    color: {ICE_WHITE};
}}
[data-testid="stHeader"] {{
    background: {MIDNIGHT_NAVY};
}}
.main .block-container {{
    max-width: 800px;
    padding-top: 3rem;
    padding-bottom: 3rem;
}}
.hero {{
    text-align: center;
    padding: 1.5rem 0 2rem;
}}
.logo {{
    display: inline-block;
    background: {SLATE_BLUE};
    color: {ELECTRIC_CYAN};
    border: 1px solid {BORDER_BLUE};
    border-radius: 18px;
    padding: 14px 22px;
    font-size: 2rem;
    margin-bottom: 12px;
}}
.hero h1 {{
    color: {ICE_WHITE};
    font-size: 2.8rem;
    font-weight: 750;
    margin: 0;
}}
.hero p {{
    color: {STEEL_GRAY};
    font-size: 1.05rem;
}}
.panel {{
    background: {DEEP_NAVY};
    border: 1px solid {BORDER_BLUE};
    border-radius: 16px;
    padding: 20px;
    margin: 12px 0;
}}
.panel-title {{
    color: {ICE_WHITE};
    font-size: 1.05rem;
    font-weight: 650;
}}
.muted {{
    color: {STEEL_GRAY};
    font-size: 0.9rem;
    margin-top: 5px;
}}
.stButton > button,
.stDownloadButton > button {{
    width: 100%;
    min-height: 3rem;
    background: {ELECTRIC_CYAN};
    color: {MIDNIGHT_NAVY};
    border: 1px solid {ELECTRIC_CYAN};
    border-radius: 10px;
    font-weight: 750;
}}
.stButton > button:hover,
.stDownloadButton > button:hover {{
    background: {ELECTRIC_CYAN};
    color: {MIDNIGHT_NAVY};
    filter: brightness(1.08);
}}
[data-testid="stAudio"] {{
    background: {SLATE_BLUE};
    border-radius: 12px;
}}
h2, h3, label, .stMarkdown {{
    color: {ICE_WHITE};
}}
hr {{
    border-color: {BORDER_BLUE};
}}
.footer {{
    text-align: center;
    color: {STEEL_GRAY};
    font-size: 0.8rem;
    margin-top: 30px;
}}
@media (max-width: 600px) {{
    .main .block-container {{
        padding: 1.5rem 1rem;
    }}
    .hero h1 {{
        font-size: 2.1rem;
    }}
}}
</style>
""", unsafe_allow_html=True)

# App heading
st.markdown("""
<div class="hero">
    <div class="logo">♫</div>
    <h1>Audio Extractor</h1>
    <p>Extract the sound. Keep the music.</p>
</div>
<div class="panel">
    <div class="panel-title">Paste your video link</div>
    <div class="muted">
        Enter a supported video URL to convert its audio into MP3.
    </div>
</div>
""", unsafe_allow_html=True)

# Check FFmpeg
if shutil.which("ffmpeg") is None:
    st.error(
        "FFmpeg was not found. Install FFmpeg and add its bin folder to PATH."
    )
    st.stop()

# Video URL input
video_url = st.text_input(
    "Video link",
    placeholder="https://example.com/video",
)

# Audio quality
quality = st.selectbox(
    "MP3 quality",
    ["128 kbps", "192 kbps", "320 kbps"],
    index=1,
)
bitrate = quality.split()[0]


def valid_url(url):
    try:
        parsed = urlparse(url.strip())
        return (
            parsed.scheme in ("http", "https")
            and bool(parsed.netloc)
        )
    except ValueError:
        return False


# Extract audio
if st.button(
    "✦  Extract Audio",
    type="primary",
    use_container_width=True,
):
    if not video_url.strip():
        st.warning("Please paste a video link first.")

    elif not valid_url(video_url):
        st.error("Please enter a valid link starting with https:// or http://.")

    else:
        with st.spinner("Downloading video and extracting audio..."):
            try:
                with tempfile.TemporaryDirectory() as temp:
                    temp_dir = Path(temp)

                    # Download the video using yt-dlp
                    options = {
                        "outtmpl": str(temp_dir / "source.%(ext)s"),
                        "format": "bestvideo*+bestaudio/best",
                        "noplaylist": True,
                        "quiet": True,
                        "no_warnings": True,
                        "retries": 2,
                        "socket_timeout": 30,
                        "max_filesize": 500 * 1024 * 1024,
                    }

                    with yt_dlp.YoutubeDL(options) as ydl:
                        info = ydl.extract_info(
                            video_url.strip(),
                            download=True,
                        )

                    # Find downloaded media
                    media_files = [
                        file for file in temp_dir.glob("source.*")
                        if file.is_file()
                        and file.suffix.lower() != ".mp3"
                    ]

                    if not media_files:
                        st.error("Could not download the video from this link.")
                        st.stop()

                    video_path = media_files[0]
                    audio_path = temp_dir / "output.mp3"

                    # Convert video audio to MP3
                    command = [
                        "ffmpeg",
                        "-hide_banner",
                        "-loglevel", "error",
                        "-y",
                        "-i", str(video_path),
                        "-vn",
                        "-codec:a", "libmp3lame",
                        "-b:a", f"{bitrate}k",
                        "-map_metadata", "-1",
                        str(audio_path),
                    ]

                    process = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        timeout=1800,
                        check=False,
                    )

                    if (
                        process.returncode != 0
                        or not audio_path.exists()
                    ):
                        st.error("Audio extraction failed.")

                        if process.stderr:
                            with st.expander("Technical details"):
                                st.code(process.stderr[-2000:])

                    else:
                        audio_data = audio_path.read_bytes()

                        if not audio_data:
                            st.error("The generated audio file is empty.")

                        else:
                            title = (info or {}).get("title") or "audio"
                            title = re.sub(
                                r'[<>:"/\\|?*\x00-\x1f]',
                                "_",
                                title,
                            ).strip(" .")

                            st.session_state["audio_result"] = {
                                "data": audio_data,
                                "name": f"{(title[:100] or 'audio')}.mp3",
                                "bitrate": bitrate,
                            }

            except yt_dlp.utils.DownloadError as error:
                st.error(
                    "Could not retrieve this video. "
                    "The website may be unsupported, the video may be "
                    "private, or access may be restricted."
                )

                with st.expander("Technical details"):
                    st.code(str(error)[-2000:])

            except subprocess.TimeoutExpired:
                st.error("Conversion timed out. Try a shorter video.")

            except Exception as error:
                st.error("Something went wrong while processing the link.")

                with st.expander("Technical details"):
                    st.code(str(error)[-2000:])


# Display extracted audio
result = st.session_state.get("audio_result")

if result:
    st.divider()

    st.markdown(f"""
    <div class="panel">
        <div class="panel-title">✓ Your MP3 is ready</div>
        <div class="muted">
            {result['name']} · {result['bitrate']} kbps
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Play audio
    st.audio(result["data"], format="audio/mpeg")

    # Download MP3
    st.download_button(
        label="↓  Download MP3",
        data=result["data"],
        file_name=result["name"],
        mime="audio/mpeg",
        type="primary",
        use_container_width=True,
    )

# Footer
st.markdown("""
<div class="footer">
    Simple, focused, and made for audio.
</div>
""", unsafe_allow_html=True)
