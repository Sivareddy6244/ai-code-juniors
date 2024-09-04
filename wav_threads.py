import wave
import threading
import time
import queue
import torch

# Assuming `fp` is the file path and `device` is the target device
# checkpoint = torch.load(weights_only=True)


def process_wav_file(handleId, filename, converter_queue):
    with wave.open(filename, 'rb') as wf:
        frame_rate = wf.getframerate()
        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()

        print(f"Processing {handleId} {filename} with {frame_rate} Hz, {channels} channels, {sample_width}-byte sample width")

        chunk_duration = 5  # seconds
        chunk_size = frame_rate * chunk_duration * channels * sample_width
        frame_data = []
        packet_id = 0

        while True:
            frames = wf.readframes(chunk_size)
            if not frames:
                break

            # Determine packet type
            if packet_id == 0:
                packet_type = 0  # Start of the chunk
            else:
                packet_type = 1  # Continuation of the chunk
            
            frame_data.append(frames)
            item = (handleId, packet_type, frame_data)
            converter_queue.put(item)
            print(f"Thread {handleId} processing packet {packet_type} for {filename}")

            time.sleep(5)  # Simulate some processing time
            packet_id += 1
        
        # Mark the last packet
        item = (handleId, 2, frame_data)  # 2 indicates the last packet
        converter_queue.put(item)
        print(f"Thread {handleId} finished processing {filename}, final packet sent.")

def start_threads(converter_queue):
    wav_files = ["TEMP/WAV/a.wav", "TEMP/WAV/b.wav", "TEMP/WAV/c.wav"]

    threads = []
    i = 0
    for filename in wav_files:
        i += 1
        thread = threading.Thread(target=process_wav_file, args=(i, filename, converter_queue))
        thread.start()
        threads.append(thread)

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print("All files have been processed.")

if __name__ == "__main__":
    converter_queue = queue.Queue()
    start_threads(converter_queue)
