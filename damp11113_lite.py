import numpy as np

class FSKEncoderV5:
    # opts = {'baud': 520+(5/6), 'space': 1562.5, 'mark': 2083+(1/3), 'sampleRate': 48000}
    def __init__(self, opts):
        if not isinstance(self, FSKEncoderV5):
            return FSKEncoderV5(opts)

        opts = opts or {}

        if 'baud' not in opts:
            raise ValueError('must specify opts.baud')
        if 'space' not in opts:
            raise ValueError('must specify opts.space')
        if 'mark' not in opts:
            raise ValueError('must specify opts.mark')
        opts['sampleRate'] = opts.get('sampleRate', 8000)
        opts['samplesPerFrame'] = opts.get('samplesPerFrame', self.getMinSamplesPerFrame(opts['sampleRate'], opts['baud']))

        self.symbolDuration = 1 / opts['baud']
        self.frameDuration = opts['samplesPerFrame'] / opts['sampleRate']
        self.state = 'preamble:space'
        self.clock = 0
        self.totalTime = 0

        self.opts = opts
        self.data = []
        self.firstWrite = True

    @staticmethod
    def getMinSamplesPerFrame(sampleRate, baud):
        return int(sampleRate / baud / 5)

    def sin(self, hz, t):
        return np.sin(np.pi * 2 * t * hz)

    def writeByte(self, b):
        data = []
        samples_per_baud = int(self.opts['sampleRate'] // self.opts['baud'])  # Calculate integer value
        for i in range(8):
            bit = b & 0x1
            b >>= 1
            data += self.sinSamples(self.opts['space'] if bit == 0 else self.opts['mark'], samples_per_baud)
        return data

    def sinSamples(self, hz, samples):
        data = []
        for i in range(samples):
            v = self.sin(hz, i / self.opts['sampleRate'])
            data.append(v)
        return data

    def writePreamble(self):
        data = self.sinSamples(self.opts['space'], self.opts['sampleRate'] // self.opts['baud'])
        data += self.sinSamples(self.opts['mark'], self.opts['sampleRate'] // self.opts['baud'])
        return data

    def transform(self, chunk):
        if isinstance(chunk, str):
            chunk = bytearray(chunk, 'utf-8')

        if self.firstWrite:
            self.data += self.writePreamble()
            self.firstWrite = False

        for i in range(len(chunk)):
            self.data += self.writeByte(chunk[i])

        frames = len(self.data) // self.opts['samplesPerFrame']
        output_frames = []
        for i in range(frames):
            idx = i * self.opts['samplesPerFrame']
            frame = self.data[idx:idx + self.opts['samplesPerFrame']]
            output_frames.append(frame)

        return output_frames

    def flush(self):
        return self.data

def preamble(samplerate=48000, baudrate=100, tone1=1000, tone2=2000, bitlist=None):
    if bitlist is None:
        bitlist = [1, 1, 0, 1, 0, 1, 0, 1]
    t = 1.0 / baudrate
    samples_per_bit = int(t * samplerate)
    byte_data = np.zeros(0)
    for _ in range(0, 16):
        for bit in bitlist:
            if bit:
                roffle = np.sin(2 * np.pi * tone2 * np.arange(samples_per_bit) / samplerate)
                byte_data = np.append(byte_data, roffle * 0.8)
            else:
                sinewave = np.sin(2 * np.pi * tone1 * np.arange(samples_per_bit) / samplerate)
                byte_data = np.append(byte_data, sinewave)

    return byte_data

def tonegen(freq, duration, samplerate=48000):
    t = np.linspace(0, duration, int(samplerate * duration), False)
    return np.sin(2 * np.pi * freq * t)

