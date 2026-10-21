
import html
import logging
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse
import streamlit as st
import yt_dlp


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Audio Extractor",
    page_icon="🎧",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# --------------------------------------------------
# COLOR PALETTE
# --------------------------------------------------

MIDNIGHT_NAVY = "#0B1220"
DEEP_NAVY = "#111C2E"
SLATE_BLUE = "#1E293B"
ELECTRIC_CYAN = "#22D3EE"
ICE_WHITE = "#F8FAFC"
STEEL_GRAY = "#94A3B8"
BORDER_BLUE = "#334155"

QUALITY_OPTIONS = {
    "128 kbps": 128,
    "192 kbps": 192,
    "320 kbps": 320,
}


# --------------------------------------------------
# CUSTOM STYLING
# --------------------------------------------------

st.markdown(
    f"""
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
        width: 100%;
        padding: 2.5rem 1.25rem;
    }}

    .hero {{
        text-align: center;
        padding: 1rem 0 1.5rem;
    }}

    .logo {{
        display: inline-block;
        background: {SLATE_BLUE};
        color: {ELECTRIC_CYAN};
        border: 1px solid {BORDER_BLUE};
        border-radius: 18px;
        padding: 12px 22px;
        font-size: 2rem;
        margin-bottom: 12px;
    }}

    .hero h1 {{
        color: {ICE_WHITE};
        font-size: clamp(2rem, 7vw, 2.8rem);
        font-weight: 750;
        margin: 0;
        overflow-wrap: anywhere;
    }}

    .hero p {{
        color: {STEEL_GRAY};
        font-size: 1rem;
        margin-top: 0.7rem;
    }}

    .panel {{
        background: {DEEP_NAVY};
        border: 1px solid {BORDER_BLUE};
        border-radius: 16px;
        padding: 18px;
        margin: 12px 0;
        overflow-wrap: anywhere;
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
        width: 100%;
        background: {SLATE_BLUE};
        border-radius: 12px;
    }}

    label, .stMarkdown, h2, h3 {{
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
            padding: 1.5rem 0.9rem;
        }}

        .panel {{
            padding: 15px;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# APP HEADING
# --------------------------------------------------

st.markdown(
    """
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
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# VIDEO URL INPUT
# --------------------------------------------------

video_url = st.text_input(
    "Video link",
    placeholder="https://example.com/video",
    help="Paste a link to a supported, accessible video.",
)


# --------------------------------------------------
# AUDIO QUALITY
# --------------------------------------------------

quality = st.selectbox(
    "MP3 quality",
    ["128 kbps", "192 kbps", "320 kbps"],
    index=1,
)

bitrate = QUALITY_OPTIONS.get(quality, 192)


# --------------------------------------------------
# URL VALIDATION
# --------------------------------------------------

def valid_url(url):
    try:
        parsed = urlparse(url.strip())

        return (
            parsed.scheme in ("http", "https")
            and bool(parsed.hostname)
            and not any(char.isspace() for char in url.strip())
        )

    except (ValueError, AttributeError):
        return False


def sanitize_title(title):
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", title or "audio")
    return cleaned.strip(" .") or "audio"


# --------------------------------------------------
# AUDIO EXTRACTION
# --------------------------------------------------

if st.button(
    "✦  Extract Audio",
    type="primary",
    use_container_width=True,
):
    st.session_state.pop("audio_result", None)

    if not video_url.strip():
        st.warning("Please paste a video link first.")

    elif not valid_url(video_url):
        st.error("Please enter a valid video URL.")

    else:
        ffmpeg_path = shutil.which("ffmpeg")

        if not ffmpeg_path:
            st.error(
                "FFmpeg is missing on the server. Add ffmpeg to the "
                "deployment's system packages and redeploy."
            )

        else:
            try:
                with st.spinner(
                    "Downloading audio and converting to MP3..."
                ):
                    with tempfile.TemporaryDirectory() as temp:
                        temp_dir = Path(temp)

                        options = {
                            "format": "bestaudio/best",
                            "outtmpl": str(
                                temp_dir / "source.%(ext)s"
                            ),
                            "noplaylist": True,
                            "quiet": True,
                            "no_warnings": True,
                            "retries": 3,
                            "fragment_retries": 3,
                            "extractor_retries": 3,
                            "socket_timeout": 30,
                            "max_filesize": 500 * 1024 * 1024,
                            "ffmpeg_location": ffmpeg_path,
                        }

                        with yt_dlp.YoutubeDL(options) as ydl:
                            info = ydl.extract_info(
                                video_url.strip(),
                                download=True,
                            )

                        downloaded_files = [
                            path
                            for path in temp_dir.iterdir()
                            if path.is_file()
                            and path.name != "audio.mp3"
                        ]
                        source_audio = max(
                            downloaded_files,
                            key=lambda path: path.stat().st_size,
                            default=None,
                        )

                        if source_audio is None:
                            raise RuntimeError(
                                "No downloadable audio was generated."
                            )

                        audio_path = temp_dir / "audio.mp3"
                        subprocess.run(
                            [
                                ffmpeg_path,
                                "-y",
                                "-i",
                                str(source_audio),
                                "-vn",
                                "-ar",
                                "44100",
                                "-ac",
                                "2",
                                "-b:a",
                                f"{bitrate}k",
                                str(audio_path),
                            ],
                            check=True,
                            capture_output=True,
                            text=True,
                        )

                        if (
                            not audio_path.is_file()
                            or audio_path.stat().st_size == 0
                        ):
                            raise RuntimeError(
                                "The MP3 file was not generated."
                            )

                        audio_data = audio_path.read_bytes()

                        title = sanitize_title(
                            (info or {}).get("title") or "audio"
                        )
                        filename = f"{title[:100]}.mp3"

                        st.session_state["audio_result"] = {
                            "data": audio_data,
                            "name": filename,
                            "bitrate": bitrate,
                        }

                st.success("Audio extracted successfully!")

            except Exception as exc:
                logging.exception("Audio extraction failed")
                st.error(
                    "Unable to extract audio from this link. "
                    "Check that the link is accessible to the hosting "
                    "server and that the deployed FFmpeg dependency is available."
                )
                details = (
                    getattr(exc, "stderr", None)
                    or getattr(exc, "msg", None)
                    or str(exc)
                )
                st.caption(f"{type(exc).__name__}: {details[-1000:]}")


# --------------------------------------------------
# DISPLAY EXTRACTED AUDIO
# --------------------------------------------------

result = st.session_state.get("audio_result")

if result:
    st.divider()

    safe_filename = html.escape(result["name"])

    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">✓ Your MP3 is ready</div>
            <div class="muted">
                {safe_filename} · {result["bitrate"]} kbps
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.audio(
        result["data"],
        format="audio/mpeg",
    )

    st.download_button(
        label="↓  Download MP3",
        data=result["data"],
        file_name=result["name"],
        mime="audio/mpeg",
        type="primary",
        use_container_width=True,
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown(
    """
    <div class="footer">
        Simple, focused, and made for audio.
    </div>
    """,
    unsafe_allow_html=True,
)
