import threading
import queue
import time
import wave
import pyaudio
from mylogs import logger
from audio_functions import *
from wav_threads import start_threads
from datetime import datetime
from pydub import AudioSegment
# import torch


# Define the message queue
recorder_thrd_queue = queue.Queue()
converter__thrd_queue = queue.Queue()
realtime_thrd_queue = queue.Queue()
passive_thrd_queue = queue.Queue()

G_INT = 0
recorder_thrd = None
converter_thrd = None
realtime_thrd = None
passive_thrd = None
recorder_thrd_event = threading.Event()

def recorder_thrd_handling(name, event, input_queue, output_queue):
    logger.debug(f"{name} is waiting for the event to be set.")
    logger.debug(f"{name} received the event. Proceeding with work...")
    filename = "abc.wav"
    sleep_duration = 90000 # Define how long you want to sleep (in seconds)

    event.wait()  # Wait until the event is set
    chunk = 1024  # Record in chunks of 1024 samples
    format = pyaudio.paInt16  # 16-bit resolution
    channels = 1  # Number of channels
    sample_rate = 44100  # Sample rate
    duration = 10  # Duration of recording in seconds
    packet_type = 0

    # Initialize PyAudio
    p = pyaudio.PyAudio()
    

    while event.is_set():
         # Open a new stream
        stream = p.open(format=format, channels=channels,
                        rate=sample_rate, input=True,
                        frames_per_buffer=chunk)

        print("Recording...")
        global G_INT 
        if G_INT == 1:
            logger.debug("recorder: Received PAUSE signal . ...\n")
            event.wait()  # Wait until the event is set
            G_INT = 0
            continue

        if G_INT == 2:
            print("recorder thread received STOP signal....")
            logger.debug("recorder: Received stop signal . ...\n")
            item_stop = (0, 2, "STOP")
            output_queue.put(item_stop)
        
            while True:
                exit_msg = input_queue.get()
                print(f"recorder received {exit_msg[2]} .... \n")
                if exit_msg[2] == "EXIT":
                    stream.stop_stream()
                    stream.close()
                    p.terminate()
                    logger.debug("Recoder:  Exiting....\n")

                    break
            break
        
        # Sleep for the defined duration before starting recording
        #time.sleep(sleep_duration)

       
        frames = []
        
    
        # Record for the specified duration
        for _ in range(0, int(sample_rate / chunk * duration)):
            data = stream.read(chunk)
            frames.append(data)
        print("Finished recording.")
        logger.debug(f"recorder: recording and sending")
        
        item_data = (0,packet_type, frames)
        packet_type = 1
        output_queue.put(item_data)
        logger.debug("recorder: sent frames . ...\n")
        stream.stop_stream()
        stream.close()

def converter_thrd_handling(name, input_queue, output_realtime_thrd_queue):
    logger.debug(f"{name} is waiting for the event to be set.")
    logger.debug(f"{name} received the event. Proceeding with work...")
    format = pyaudio.paInt16  # 16-bit resolution
    channels = 1  # Number of channels
    sample_rate = 44100  # Sample rate
    p = pyaudio.PyAudio()
    
    while True:
        item = input_queue.get()
        handleId = item[0]
        packet_type = item [1]
        frames = item[2]
        if frames == "STOP":
            logger.debug("converter: Received stop signal. waiting...\n")
            output_realtime_thrd_queue.put(item)
            while True:
                    exit_msg = input_queue.get()
                    if (exit_msg[2]=="EXIT"):
                        logger.debug("Converter:  Exiting....\n")
                        break
            break
        logger.debug(f"converter: Converting packet {packet_type} for handler {handleId}.")

        # Save the recording as a WAV file
        # Save the recording as a WAV file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output_wav = f"TEMP/WAV/temp_{timestamp}.wav"
        output_file = f"TEMP/MP3/output_{timestamp}.mp3"
        if frames :
            wf = wave.open(output_wav, 'wb')
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(format))
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(frames))
            wf.close()
        # Convert the WAV file to MP3
            audio = AudioSegment.from_wav(output_wav)
            audio.export(output_file, format="mp3")
        
        output_item = (handleId, packet_type, output_file)
        output_realtime_thrd_queue.put(output_item)



def getTranscription(transcription_result):
    if isinstance(transcription_result, dict):
                transcription = transcription_result.get('text', '')
    elif isinstance(transcription_result, str):
                transcription = transcription_result
    else:
                logger.warning(f"Warning: Transcription result for is not in the expected format. Skipping.")
                transcription = '' 
    return transcription
    

def realtime_thrd_handling(name, input_queue, output_passive_thrd_queue):
    logger.debug(f"{name} is waiting for the event to be set.")
    logger.debug(f"{name} received the event. Proceeding with work...")
    logger.debug("realtime_thrd started")
    
    while True:
        item = input_queue.get()
        handleId = item[0]
        packet_type = item [1]
        file_location = item[2]
    
        logger.debug(f"realtime_thrd: Processing packet {packet_type} for handler {handleId}.")
        
        if file_location == "STOP":
            logger.debug("Realtime: Received stop signal. waiting for exit...\n")
            output_passive_thrd_queue.put(item)
 
            while True:
                 exit_msg = input_queue.get()
                 if ( exit_msg[2]=="EXIT"):
                        logger.debug("Realtime:  Exiting....\n")
                        break
            break
        transcription_result = transcribeAudio(file_location)
        transcription = getTranscription(transcription_result)
        result= analyze_sentiment_and_aggression(transcription)
        print(f"Realtime: sentiment and aggression :: {result}...\n")
        logger.debug(f"Realtime: sentiment and aggression {result}...\n")
        output_item = (handleId, packet_type, transcription)
        output_passive_thrd_queue.put(output_item)


def performMEetingSummary(handler_id,transSummary) :
       summary= meetiningNotesSummariser(transSummary)
       print(f"meeting summary:: {handler_id}{summary}\n")
       logger.debug(f"meeting summary .... {handler_id}::{summary}   \n")
       return summary


def passive_thrd_handling(name,input_queue, recoder_thread_queue, converter_thread_queue, realtime_thread_queue):
    logger.debug(f"{name} is waiting for the event to be set.")
    logger.debug(f"{name} received the event. Proceeding with work...")
    transcribe_wishper_list =[]
    transcription_summary_handle_ids=["", "", "", "", "", "","","","",""]
    while True:

        # Receive message from the queue
        print(" PASSIVE THREAD WHILE LOOP")
        item = input_queue.get()
        file_location = item[2]
        packet_type = item[1]
        handler_id = item[0]
        print(f"passive: got data for handler:: {item[0]} {item[1]} data::{file_location}")
        if file_location == "SUMMARY":
            print(f"passive: Received SUMMARY event...from {item[0]}\n")
            summary = performMEetingSummary(handler_id,transcription_summary_handle_ids[handler_id]) 
            print(summary)

            continue
        
    
        if file_location == "STOP":
            
            logger.debug("passive: Received STOP event . ...\n")
            logger.debug(transcribe_wishper_list)
            #logger.debug(transcribe_assembly_ai_list)
            logger.debug("passive: sending EXIT to other threads . ...\n")
            exit_item = (item[0], 2 , "EXIT")
            recoder_thread_queue.put(exit_item)
            realtime_thread_queue.put(exit_item)
            converter_thread_queue.put(exit_item)
            time.sleep(5)
            logger.debug("passive: Exiting  . ...\n")
            break
        """
        transcription_result=transcribeAudio(file_location)
        transcription =getTranscription(transcription_result)
        print(f"passive thread- transcribe::: {transcription}...\n")
        """
        if (packet_type==0):
            transcription_summary_handle_ids[handler_id]= file_location

        elif (packet_type ==1) :
            transcription_summary_handle_ids[handler_id]= transcription_summary_handle_ids[handler_id] + " " + file_location
        else  :
              transcription_summary_handle_ids[handler_id]= transcription_summary_handle_ids[handler_id] + " " + file_location
              summary = performMEetingSummary(handler_id,transcription_summary_handle_ids[handler_id])
              print(summary)
        
        #transcribe_wishper_list.append(file_location)
        #input_events_list.append(item)
        #result_wishper=transcribeAudio(file_location)
       # transcribe_wishper_list.append(result_wishper)
       
       
       



def initAudio():
    global recorder_thrd, converter_thrd, realtime_thrd, passive_thrd
    
    recorder_thrd = threading.Thread(target=recorder_thrd_handling, args=("RECODER_THRD",
                     recorder_thrd_event,
                     recorder_thrd_queue,
                     converter__thrd_queue
                     ))
    converter_thrd = threading.Thread(target=converter_thrd_handling, args=("CONVERTER_THRD",
            converter__thrd_queue,
            realtime_thrd_queue
            ))
    realtime_thrd = threading.Thread(target=realtime_thrd_handling, args=("REALTIME_THRD",
            realtime_thrd_queue,
            passive_thrd_queue
            ))
    passive_thrd = threading.Thread(target=passive_thrd_handling, args=("PASSIVE_THRD",
            passive_thrd_queue,
            recorder_thrd_queue,
            converter__thrd_queue,
            realtime_thrd_queue
            ))
    recorder_thrd.start()
    converter_thrd.start()
    realtime_thrd.start()
    passive_thrd.start()
    
def terminateAudio(recorder_thrd, converter_thrd, realtime_thrd, passive_thrd):
    recorder_thrd.join()
    converter_thrd.join()
    realtime_thrd.join()
    passive_thrd.join()
    recorder_thrd_queue.queue.clear()
    converter__thrd_queue.queue.clear()
    realtime_thrd_queue.queue.clear()
    passive_thrd_queue.queue.clear()

    print("Main: all threads have finished.")

def start_recording():
    recorder_thrd_event.set()
    
def pause_recording():
    global G_INT
    G_INT = 1
    
def stop_rcording():
    global G_INT
    G_INT = 2
    time.sleep(12)
    terminateAudio(recorder_thrd, converter_thrd, realtime_thrd, passive_thrd)

def get_summary(handler_id):
    print("sending SUMMARY event to PASSIVE THREAD\n")
    item = (handler_id,1, "SUMMARY")
    passive_thrd_queue.put(item)

if __name__ == "__main__":
    initAudio()
    time.sleep(3)
    start_recording()
    time.sleep(5)
    start_threads(converter__thrd_queue)
    k = 2
    while k < 4:
        k += 1 
        time.sleep(10)
        get_summary(0)

    time.sleep(10)
    stop_rcording()
    time.sleep(3)