"""ACTR class"""

import os
import boto3
import hashlib
import logging
import hashlib                
from bbot.core import BBotLoggerAdapter

class ACTR():

    def __init__(self, config: dict, dotbot: dict) -> None:
        """Initializes class"""
        self.config = config
        self.dotbot = dotbot
        self.logger_level = ''

        self.visemes = None
        
        self.logger = BBotLoggerAdapter(logging.getLogger('actr'), self, self, 'actr')        

    def init(self, core):
        """Initializes some values"""
        pass
        

    def get_actr(self, text: str, locale: str, voice_id: str, time_scale: int):
        """
        """
        
        # get visemes
        self.visemes.voice_locale = locale
        self.visemes.voice_id = voice_id
        visemes = self.visemes.get_visemes(text, time_scale)
        
        # fixes amazon polly response
        # adds a start delay and provides duration for each viseme
        first = True 
        new_visemes = []
        start_delay = 0       
        for idx, v in enumerate(visemes):                                    
            # if this is the first viseme then time is start_delay value                
            if first: 
                start_delay = v['time'] 
                first = False
                        
            if idx == len(visemes) - 1:
                # this is the last viseme. let duration as the median of previous viseme duration
                # @TODO
                duration = 100
            else:                
                # get duration by the substraction of next viseme time and current time
                next_t = visemes[idx + 1]['time']
                duration = next_t - v['time']
                        
            new_visemes.append({'value': v['value'], 'duration': duration})

        new_visemes.insert(0,{'value': 'sil', 'duration': start_delay})
        response = {
           'visemes': new_visemes
        }

        self.logger.debug('Visemes:' + str(response))
        return response
   