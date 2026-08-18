from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings


class ElevenLabsTTS:

    def __init__(self, api_key, voice_id, model_id):
        self.client = ElevenLabs(api_key=api_key)
        self.voice_id = voice_id
        self.model_id = model_id

    def speak(self, text: str):
        audio = self.client.text_to_speech.convert(
            voice_id=self.voice_id,
            model_id=self.model_id,
            output_format="mp3_22050_32",
            text=text,
            voice_settings=VoiceSettings(
                stability=0.0,
                similarity_boost=1.0,
                style=0.0,
                use_speaker_boost=True,
                speed=1.0,
            ),
        )

        for chunk in audio:
            if chunk:
                # connect this to your existing audio playback
                ...