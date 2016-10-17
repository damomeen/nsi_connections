# Copyright 2016 Poznan Supercomputing and Networking Center (PSNC)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def start_stop_time():
    start = datetime.utcnow()
    epoch = datetime.utcfromtimestamp(0) 
    delta = start - epoch
    start_sec = int(delta.total_seconds()) +10 # setup 30 sec delay
    end_sec = start_sec + 60*60 # Connection for 1 hour
    return start_sec, end_sec
    
    
def convert_to_seconds(utc_time_iso):
    import pytz
    utc = pytz.timezone('Etc/Greenwich')
    epoch = datetime.utcfromtimestamp(0) 
    epoch = utc.localize(epoch)
    epoch.astimezone(pytz.utc)
    delta = utc_time_iso - epoch
    return int(delta.total_seconds())
    
    
def convert_to_utc(local_time_iso):
    import isodate
    import pytz
    dt = isodate.parse_datetime(local_time_iso) # is able to parse many datatime formats
    dt.astimezone(pytz.utc)  # convert datatime from local to UTC
    logger.debug('Converting time from local (%s) to UTC (%s)', dt, dt.strftime('%Y-%m-%d %H:%M:%SZ'))
    return dt
    

def time_constrains(start_time, end_time):
    start_sec, end_sec = -1, -1   # values '-1' means that given time attribute is not specified
    
    # if start_time and end_time specified, use them
    if start_time:
        start_time = convert_to_utc(start_time)
        start_sec = convert_to_seconds(start_time) + 10 # add 10 sec for software to be able to process the request
    if end_time:
        end_time = convert_to_utc(end_time)
        end_sec = convert_to_seconds(end_time)
    
    # if start_time and end_time not specified, generate them
    if not start_time or not end_time:
        start_sec, end_sec = start_stop_time()
        
    return start_sec, end_sec