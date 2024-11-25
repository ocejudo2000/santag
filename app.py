import gradio as gr
import edge_tts
import asyncio
import tempfile
import os
import ftplib

# FTP Configuration
FTP_HOST = 'ftp.nitrodata.com.mx'
FTP_PORT = 21
FTP_USER = 'ocejudo@nitrodata.com.mx'
FTP_PASS = 'OrionPaola2$#'
FTP_DIR = '/public_html/ocejudo'  # Path in the FTP server
BASE_URL = "http://nitrodata.com.mx/ocejudo/"  # Base public URL for the uploaded files

# Get all available voices
async def get_voices():
    voices = await edge_tts.list_voices()
    return {f"{v['ShortName']} - {v['Locale']} ({v['Gender']})": v['ShortName'] for v in voices}

# Function to upload the file to the FTP server
def upload_to_ftp(local_file):
    try:
        # Connect to the FTP server
        ftp = ftplib.FTP()
        ftp.connect(FTP_HOST, FTP_PORT)
        ftp.login(FTP_USER, FTP_PASS)
        ftp.cwd(FTP_DIR)

        # Get the file name from the local file path
        file_name = os.path.basename(local_file)

        # Upload the file
        with open(local_file, 'rb') as file:
            ftp.storbinary(f"STOR {file_name}", file)

        print(f"File {file_name} successfully uploaded to {FTP_DIR}")
        ftp.quit()

        # Return the full public URL of the file
        return f"{BASE_URL}{file_name}"
    except Exception as e:
        print(f"Failed to upload file: {e}")
        return None

# Text-to-speech function
async def text_to_speech(text, voice, rate, pitch):
    if not text.strip():
        return None, None, gr.Warning("Please enter text to convert.")
    if not voice:
        return None, None, gr.Warning("Please select a voice.")
    
    voice_short_name = voice.split(" - ")[0]
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"
    communicate = edge_tts.Communicate(text, voice_short_name, rate=rate_str, pitch=pitch_str)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tmp_path = tmp_file.name
        await communicate.save(tmp_path)

    # Upload the generated audio file to the FTP server
    file_url = upload_to_ftp(tmp_path)

    return tmp_path, file_url, None

# Gradio interface function
def tts_interface(text, voice, rate, pitch):
    audio, file_url, warning = asyncio.run(text_to_speech(text, voice, rate, pitch))
    if file_url:
        return audio, f"[Click here to access your audio file]({file_url})", warning
    return audio, None, warning

# Create Gradio application
async def create_demo():
    voices = await get_voices()
    
    description = """
    Convert text to speech using Microsoft Edge TTS. Adjust speech rate and pitch: 0 is default, positive values increase, negative values decrease.
    
    🎥 **Exciting News: Introducing our Text-to-Video Converter!** 🎥
    
    Take your content creation to the next level with our cutting-edge Text-to-Video Converter! 
    Transform your words into stunning, professional-quality videos in just a few clicks. 
    
    ✨ Features:
    • Convert text to engaging videos with customizable visuals
    • Choose from 40+ languages and 300+ voices
    • Perfect for creating audiobooks, storytelling, and language learning materials
    • Ideal for educators, content creators, and language enthusiasts
    
    Ready to revolutionize your content? [Click here to try our Text-to-Video Converter now!](https://text2video.wingetgui.com/)
    """
    
    demo = gr.Interface(
        fn=tts_interface,
        inputs=[
            gr.Textbox(label="Input Text", lines=5),
            gr.Dropdown(choices=[""] + list(voices.keys()), label="Select Voice", value=""),
            gr.Slider(minimum=-50, maximum=50, value=0, label="Speech Rate Adjustment (%)", step=1),
            gr.Slider(minimum=-20, maximum=20, value=0, label="Pitch Adjustment (Hz)", step=1)
        ],
        outputs=[
            gr.Audio(label="Generated Audio", type="filepath"),
            gr.Markdown(label="Download Link"),
            gr.Markdown(label="Warning", visible=False)
        ],
        title="Edge TTS Text-to-Speech",
        description=description,
        article="Experience the power of Edge TTS for text-to-speech conversion, and explore our advanced Text-to-Video Converter for even more creative possibilities!",
        analytics_enabled=False,
        allow_flagging="manual"
    )
    return demo

# Run the application
if __name__ == "__main__":
    demo = asyncio.run(create_demo())
    demo.launch()
