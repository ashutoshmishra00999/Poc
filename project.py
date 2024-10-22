import os
import streamlit as st
import moviepy.editor as mp
from google.cloud import speech, texttospeech
import openai
import tempfile

# Set up Google Cloud APIs for Speech-to-Text and Text-to-Speech and Download the service account key JSON file. and put that json file here
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/to/your/google_credentials.json" 
openai.api_key = '22ec84421ec24230a3638d1b51e3a7dc'

def transcribe_audio(video_file):

    audio_clip = mp.VideoFileClip(video_file).audio
    audio_path = tempfile.mktemp(suffix=".wav")
    audio_clip.write_audiofile(audio_path, codec='pcm_s16le')

    client = speech.SpeechClient()
    with open(audio_path, "rb") as audio_file:
        content = audio_file.read()
    
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )

    response = client.recognize(config=config, audio=audio)
    transcription = " ".join(result.alternatives[0].transcript for result in response.results)
    
    return transcription

def correct_transcription(transcription):

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": f"Correct the following text for grammar: {transcription}"}]
    )
    return response['choices'][0]['message']['content']

def generate_audio(text):
    """Generate audio from text using Google Text-to-Speech."""
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Wavenet-D", 
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
    )

    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

    audio_path = tempfile.mktemp(suffix=".wav")
    with open(audio_path, "wb") as out:
        out.write(response.audio_content)

    return audio_path

def replace_audio_in_video(video_file, new_audio_path):

    video_clip = mp.VideoFileClip(video_file)
    new_audio_clip = mp.AudioFileClip(new_audio_path)
    final_video = video_clip.set_audio(new_audio_clip)
    
    output_path = tempfile.mktemp(suffix=".mp4")
    final_video.write_videofile(output_path, codec='libx264', audio_codec='aac')
    
    return output_path

def main():
    st.title("Video Audio Replacement with AI")
    uploaded_file = st.file_uploader("Choose a video file...", type=["mp4", "mov", "avi"])
    
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(uploaded_file.read())
            video_path = tmp_file.name
        
        st.video(video_path)

        if st.button("Process Video"):
            transcription = transcribe_audio(video_path)
            st.write("Transcription:", transcription)

            corrected_text = correct_transcription(transcription)
            st.write("Corrected Transcription:", corrected_text)

            new_audio_path = generate_audio(corrected_text)
            st.write("Generated Audio File Path:", new_audio_path)

            final_video_path = replace_audio_in_video(video_path, new_audio_path)
            st.write("Final Video File Path:", final_video_path)
            st.video(final_video_path)

if __name__ == "__main__":
    main()
