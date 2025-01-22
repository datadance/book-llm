# 录音
import webrtcvad
import collections
import sys
import signal
import pyaudio
from array import array
from struct import pack
import wave
import time


# recoding
class AudioRecord:
    def __init__(self):
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK_DURATION_MS = 20  # supports 10, 20 and 30 (ms)
        self.PADDING_DURATION_MS = 1500  # 1 sec jugement
        self.CHUNK_SIZE = int(self.RATE * self.CHUNK_DURATION_MS / 1000)  # chunk to read
        self.CHUNK_BYTES = self.CHUNK_SIZE * 2  # 16bit = 2 bytes, PCM
        self.NUM_PADDING_CHUNKS = int(self.PADDING_DURATION_MS / self.CHUNK_DURATION_MS)
        # NUM_WINDOW_CHUNKS = int(240 / CHUNK_DURATION_MS)
        self.NUM_WINDOW_CHUNKS = int(400 / self.CHUNK_DURATION_MS)  # 400 ms/ 30ms  ge
        self.NUM_WINDOW_CHUNKS_END = self.NUM_WINDOW_CHUNKS * 2
        self.START_OFFSET = int(self.NUM_WINDOW_CHUNKS * self.CHUNK_DURATION_MS * 0.5 * self.RATE)

        self.vad = webrtcvad.Vad(2)  # 0, 1, 2, 3

        pa = pyaudio.PyAudio()
        self.stream = pa.open(format=self.FORMAT,
                              channels=self.CHANNELS,
                              rate=self.RATE,
                              input=True,
                              start=False,
                              # input_device_index=2,
                              frames_per_buffer=self.CHUNK_SIZE)
        self.got_a_sentence = False
        signal.signal(signal.SIGINT, self.handle_int)

    def handle_int(self, sig, chunk):
        global leave, got_a_sentence
        leave = True
        got_a_sentence = True

    def normalize(self, snd_data):
        "Average the volume out"
        MAXIMUM = 32767  # 16384
        times = float(MAXIMUM) / max(abs(i) for i in snd_data)
        r = array('h')
        for i in snd_data:
            r.append(int(i * times))
        return r

    def record_audio(self, save_audio=True, audio_cache_path='./data/recording/cache.wav'):
        """
        Recording, return audio data, or save to an audio file
        :param save_audio: True or False, save the recording file
        :param audio_cache_path: Path to saved audio recording file
        :return: Voice signal list data for speech
        """
        ring_buffer = collections.deque(maxlen=self.NUM_PADDING_CHUNKS)
        triggered = False
        voiced_frames = []
        ring_buffer_flags = [0] * self.NUM_WINDOW_CHUNKS
        ring_buffer_index = 0
        ring_buffer_flags_end = [0] * self.NUM_WINDOW_CHUNKS_END
        ring_buffer_index_end = 0
        buffer_in = ''
        raw_data = array('h')
        index = 0
        start_point = 0
        StartTime = time.time()
        print("开始聆听......")
        self.stream.start_stream()
        got_a_sentence = False
        while not got_a_sentence:
            chunk = self.stream.read(self.CHUNK_SIZE)
            # add WangS
            raw_data.extend(array('h', chunk))
            index += self.CHUNK_SIZE
            TimeUse = time.time() - StartTime
            active = self.vad.is_speech(chunk, self.RATE)

            sys.stdout.write('-' if active else '_')
            ring_buffer_flags[ring_buffer_index] = 1 if active else 0
            ring_buffer_index += 1
            ring_buffer_index %= self.NUM_WINDOW_CHUNKS

            ring_buffer_flags_end[ring_buffer_index_end] = 1 if active else 0
            ring_buffer_index_end += 1
            ring_buffer_index_end %= self.NUM_WINDOW_CHUNKS_END

            # start point detection
            if not triggered:
                ring_buffer.append(chunk)
                num_voiced = sum(ring_buffer_flags)
                if num_voiced > 0.8 * self.NUM_WINDOW_CHUNKS:
                    sys.stdout.write(' Open ')
                    triggered = True
                    start_point = index - self.CHUNK_SIZE * 20  # start point
                    ring_buffer.clear()
            # end point detection
            else:
                ring_buffer.append(chunk)
                num_unvoiced = self.NUM_WINDOW_CHUNKS_END - sum(ring_buffer_flags_end)
                if num_unvoiced > 0.90 * self.NUM_WINDOW_CHUNKS_END or TimeUse > 10:
                    sys.stdout.write(' Close ')
                    triggered = False
                    got_a_sentence = True
            sys.stdout.flush()

        sys.stdout.write('\n')
        self.stream.stop_stream()
        # write to file
        raw_data.reverse()
        for index in range(start_point):
            raw_data.pop()
        raw_data.reverse()
        raw_data = self.normalize(raw_data)
        if save_audio:
            wave_out = wave.open(audio_cache_path, 'wb')
            wave_out.setnchannels(1)
            wave_out.setsampwidth(2)
            wave_out.setframerate(16000)
            wave_out.writeframes(raw_data)
            wave_out.close()

        # print("* done recording")

        return raw_data


if __name__ == '__main__':
    path = './data/cache/record_cache.pcm'
    AR = AudioRecord()
    data = AR.record_audio(save_audio=True, audio_cache_path=path)
    print(data)
