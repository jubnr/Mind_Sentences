import wave, csv

def send_trigger():
    pp.set_data(255)
    # wait for 50ms
    end_time = time.perf_counter() + 0.05   
    while time.perf_counter() < end_time:
        pass
    pp.set_data(0)

def get_audio_duration(audio_path):
    with wave.open(audio_path, 'rb') as audio_file:
        frames = audio_file.getnframes()
        rate = audio_file.getframerate()
        duration = frames / float(rate)
        return duration 
    
def save_response(sub, audio_path, response_start_time, response_end_time, time_took, audio_duration, accuracy):
    csv_filename = f"data/responses_sub-{sub}.csv"
    
    with open(csv_filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        
        if file.tell() == 0: 
            writer.writerow(["subject_id", "audio", "response_start_time (s)", "response_end_time (s)", "time_took (s)", "audio_duration (s)", "accuracy (%)"])
        writer.writerow([sub, audio_path, response_start_time, response_end_time, time_took, audio_duration, accuracy])