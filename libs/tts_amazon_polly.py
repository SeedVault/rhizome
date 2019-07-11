"""TTS wrapper class"""

import os
import boto3
import hashlib
import logging
import hashlib                
import json

class TTSAmazonPolly():

    def __init__(self, config: dict, dotbot: dict) -> None:
        """Initializes class"""
        self.config = config
        self.dotbot = dotbot
        self.voice_id = 1
        self.voice_locale = 'en_US'
        self.tts_service_name = 'AmazonPolly'

        # https://docs.aws.amazon.com/polly/latest/dg/voices-in-polly.html
        self.voice_id_locale_map = {
            'en_US': ['Joanna', 'Ivy', 'Kendra', 'Kimberly', 'Salli', 'Joey', 'Justin', 'Matthew']
        }


        self.logger = logging.getLogger("tts")
    
    def get_speech_audio_url(self, text: str, scale_time: int=100) -> str:
        """Returns audio file url with speech synthesis"""

        text = self.set_scaletime(text, scale_time)

        filename = self.get_audio_filename(text)

        self.logger.debug('Providing voice audio file "' + filename + '"')

        # check if audio file is available in cache folder
        exists = os.path.isfile(self.get_file_full_path(filename))
        if not exists:
            self.gen_speech_audio(text, filename)

        return self.config['cache_web_url'] + filename

    def gen_speech_audio(self, text: str, filename: str) -> bool:
        """Calls TTS service and places the audio file somewhere"""

        polly_client = boto3.Session(
                aws_access_key_id = self.config['aws_access_key_id'],                     
                aws_secret_access_key = self.config['aws_secret_access_key'],
                region_name = self.config['aws_region_name']).client('polly')

        voice_id = self.get_amazonpolly_voice_id_from_locale()
        
        # convert symbols to text (< 'less than', > 'greater than', etc)
        text = self.convert_symbols(text)

        self.logger.debug('Requesting speech audio to Amazon Polly voice id "' + voice_id + '" - Text: "' + text + '"')
        response = polly_client.synthesize_speech(                    
                    VoiceId = voice_id,
                    OutputFormat='mp3', 
                    TextType='ssml',
                    Text = text)

        self.logger.debug("Amazon Polly reponse: " + str(response))

        if response.get('AudioStream', None):
            file = open(self.get_file_full_path(filename), 'wb')
            file.write(response['AudioStream'].read())
            file.close()
            return True

        return False

    def get_filename(self, text: str) -> str:
        """Returns filename based on the text hash and prefixes tts service name and voice locale and voice id"""    
        hash_object = hashlib.md5(text.encode())
        return self.tts_service_name + '_' + self.voice_locale + '_' + str(self.voice_id) + '_' + hash_object.hexdigest()

    def get_audio_filename(self, text: str) -> str:
        """Returns filename based on the text hash and prefixes tts service name and voice locale and voice id and format type"""    
        return self.get_filename(text) + '.mp3'
        
    def get_file_full_path(self, filename: str) -> str:
        """Returns audio file full path"""
        return self.config['cache_local_path'] + '/' + filename
        
    def get_amazonpolly_voice_id_from_locale(self) -> str:
        """Returns voice id based on locale and bbot voice id
            If no valid voice id is provided will default to id 1"""
        return self.voice_id_locale_map[self.voice_locale][int(self.voice_id)]

    def convert_symbols(self, text: str) -> str:
        """Convert symbols to text (< 'less than', > 'greater than', etc) 
        @TODO multilanguage support
        @TODO check previous comas
        """
        text = text.replace('&lt;', ', less than symbol, ')
        text = text.replace('&gt;', ', greater than symbol, ')
        text = text.replace('[', ', open square brackets, ')
        text = text.replace(']', ', close sqare brackets, ')
        text = text.replace('{', ', open curly brackets, ')
        text = text.replace('}', ', close curly brackets, ')
        text = text.replace('(', ', open parenthesis, ')
        text = text.replace(')', ', close parenthesis, ')        
        text = text.replace('&quot', ', quotes, ')
        text = text.replace('&#x27;', '')        
        text = text.replace('$', ', $ symbol, ')        # @TODO this should convert values like $123 into '123 dollars'
        return text

    def set_scaletime(self, text, scale_time: int=100) -> str:
        """Parses the ssml to adjust all timescales on it"""
        #@TODO
        return '<speak><prosody rate="' + str(scale_time) + '%">' + text + '</prosody></speak>'