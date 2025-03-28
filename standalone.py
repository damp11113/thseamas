import subprocess
import time
import dearpygui.dearpygui as dpg
import numpy as np
import pyttsx3
from datetime import datetime
import pyaudio
import json
from scipy import signal
import soundfile as sf
import threading
import scipy.fftpack as fft
import os
from damp11113_lite import FSKEncoderV5, preamble, tonegen

from ui import ui

version = "1.6"

def findkeybyvalue(data, value_to_find_key):
    return list(data.keys())[list(data.values()).index(value_to_find_key)]

def resample_and_convert_to_mono(audio_data, file_sample_rate, target_sample_rate=48000):
    # Resample the audio data
    resampled_audio = signal.resample(audio_data, int(len(audio_data) * target_sample_rate / file_sample_rate))

    # If the resampled audio is stereo, convert it to mono
    if len(resampled_audio.shape) > 1 and resampled_audio.shape[1] == 2:
        # Convert stereo to mono by averaging left and right channels
        mono_audio = np.mean(resampled_audio, axis=1)
    else:
        # If already mono or different channel configuration, keep it as is
        mono_audio = resampled_audio

    return mono_audio

class App:
    def __init__(self):
        self.sender = "THsEAmaS" # change your call sign or name of station
        # use "python -m sounddevice" to scan device name
        self.device_name_input = "" # microphone input
        self.device_name_input_EAS = "CABLE Output (VB-Audio Virtual " # microphone input from receiver
        self.device_name_output = "CABLE Input (VB-Audio Virtual C" # output to mixer or processor

        self.enableTHvoice = False # Beta
        self.sample_rate = 48000

        # Dont touch (System variables)
        self.ttsfromtext = False
        self.currentwavaudiomessagepath = ""
        self.currentiswaitvoiceaudiomessage = False
        self.currentiswaitvoiceaudiomessagerecord = False
        self.currentvoicemessagesdata = []
        self.encoderopts = {'baud': 520+(5/6), 'space': 1562.5, 'mark': 2083+(1/3), 'sampleRate': self.sample_rate}
        self.eventlist = {}
        self.currentitemcountlist = 0
        self.area = ["All", "Center", "North", "South", "East", "West", "Northeast", "Southeast", "Southwest", "Northwest"]
        self.audiomessagetype = "No Audio"
        self.ishasaudiomessage = False
        self.eventdata = None
        self.thailanddata = None
        self.paudio = None
        self.filter_b, self.filter_a = None, None
        self.ui = None
        self.decoder_process = None
        self.isrecordrecevicer = False
        self.latest_part_time_decoder = 0
        self.delay_detect_tone = 0
        self.decoder_is_boardcast = False

    def clearlist(self, sender, data):
        dpg.configure_item("clearlistwarningpopup", show=False)

        for i in range(self.currentitemcountlist):
            dpg.delete_item(f"Eventzonelistrow{i}")
        self.currentitemcountlist = 0
        self.eventlist = {}

    def startbroadcast(self, EASc=None):
        try:
            self.audiomessagetype = dpg.get_value("encoderaudiomessagetypeinput")
            dpg.configure_item("broadcastwarningpopup", show=False)
            dpg.configure_item("encoderbroadcastbutton", show=False)

            dpg.configure_item("statusbar", default_value="Encoding EAS", color=(255, 255, 0))

            if not EASc:
                EAScode = []
                EAScode.append("ZCZC")
                EAScode.append(str(dpg.get_value("encoderORGinput")).split("[")[1].split("]")[0])
                EAScode.append(str(dpg.get_value("encoderEventinput")).split(" ")[1].split("[")[1].split("]")[0])

                if len(self.eventlist.items()) == 0:
                    dpg.configure_item("statusbar", default_value="Invalid Data", color=(255, 0, 0))
                    dpg.configure_item("encoderbroadcastbutton", show=True)
                    time.sleep(1)
                    dpg.configure_item("statusbar", default_value="Ready", color=(0, 255, 0))
                    return

                for c, (prov, area) in enumerate(self.eventlist.items()):
                    areacode = f"{self.area.index(area)}{self.thailanddata.get(prov)}066"

                    if c + 1 == len(self.eventlist):
                        tpurge = dpg.get_value("encodertimepurgeinput")
                        areacode += "+" + str(tpurge.get("hour")).zfill(2) + str(tpurge.get("min")).zfill(2)

                    EAScode.append(areacode)


                EAScode.append(datetime.now().strftime("%j%H%M"))
                EAScode.append(self.sender)
                EASc = "-".join(EAScode) + "-END"
                altone = None
                Audio_messages = None

                if self.audiomessagetype in ["TTS", "WAV", "No Audio"]:
                    if dpg.get_value("encodertonetypeinput") == "NWS (1050 Hz)":
                        altone853 = tonegen(853, 5)
                        altone960 = tonegen(960, 5)
                        altone = np.concatenate([((altone853 + altone960) * 0.5), tonegen(1050, 5)])
                    elif dpg.get_value("encodertonetypeinput") == "EAS (853/960 Hz)":
                        altone853 = tonegen(853, 5)
                        altone960 = tonegen(960, 5)
                        altone = ((altone853 + altone960) * 0.5)
                    else:
                        altone = None

                    if self.audiomessagetype == "TTS":
                        dpg.configure_item("statusbar", default_value="Generate Voice", color=(255, 255, 0))
                        engine = pyttsx3.init()
                        engine.setProperty('volume', 10)  # Volume 0-1
                        engine.setProperty('rate', 148)  # 148
                        if self.enableTHvoice:
                            engine.setProperty('voice',
                                               "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_THAI")  # thai lang
                        engine.save_to_file(dpg.get_value("encoderaudiomessagetypettsmessageinput"), "tempttsmessage.wav")

                        engine.runAndWait()

                        with sf.SoundFile("tempttsmessage.wav", 'r') as file:
                            file_sample_rate = file.samplerate
                            audio_data = file.read()

                        os.remove("tempttsmessage.wav")

                        Audio_messages = resample_and_convert_to_mono(audio_data, file_sample_rate)

                    elif self.audiomessagetype == "WAV":
                        dpg.configure_item("statusbar", default_value="Reading WAV", color=(255, 255, 0))
                        with sf.SoundFile(self.currentwavaudiomessagepath, 'r') as file:
                            file_sample_rate = file.samplerate
                            audio_data = file.read()

                        Audio_messages = resample_and_convert_to_mono(audio_data, file_sample_rate)
                    else:
                        Audio_messages = None
                else:
                    if self.audiomessagetype == "Voice (from mic)":
                        dpg.configure_item("statusbar", default_value="Starting record", color=(255, 255, 0))
                        self.currentiswaitvoiceaudiomessage = True
                        self.currentiswaitvoiceaudiomessagerecord = True
                        reast = threading.Thread(target=self.recordaudiomessagevoice)
                        reast.start()
                        Audio_messages = "waitvoice"
                        altone = None
            else:
                dpg.configure_item("statusbar", default_value="Detecting tone", color=(255, 255, 0))
                time.sleep(self.delay_detect_tone + 1)
                # output = self.detecttone()
                # print(output)
                # if output == 1:
                #     altone853 = tonegen(853, 5)
                #     altone960 = tonegen(960, 5)
                #     altone = ((altone853 + altone960) * 0.5)
                # else:
                #     dpg.configure_item("encoderbroadcastbutton", show=True)
                #     dpg.configure_item("statusbar", default_value="Ready", color=(0, 255, 0))
                #     self.decoder_is_boardcast = True
                #     return

                altone853 = tonegen(853, 3)
                altone960 = tonegen(960, 3)
                altone = ((altone853 + altone960) * 0.5)
                Audio_messages = "waitvoicerecevice"


            encoder = FSKEncoderV5(self.encoderopts)
            encoder.firstWrite = False  # disable builtin preamp

            EASpreamble = preamble(baudrate=520 + (5 / 6), tone1=1562.5, tone2=2083 + (1 / 3))

            Header = np.concatenate((EASpreamble, np.concatenate(encoder.transform(EASc))))

            encoder2 = FSKEncoderV5(self.encoderopts)
            encoder2.firstWrite = False  # disable builtin preamp

            EOM = np.concatenate((EASpreamble, np.concatenate(encoder2.transform("NNNNTH"))))

            # apply filter
            Header = signal.filtfilt(self.filter_b, self.filter_a, Header)
            EOM = signal.filtfilt(self.filter_b, self.filter_a, EOM)

            # clip
            Header = np.clip(Header, -1.0, 1.0)
            EOM = np.clip(EOM, -1.0, 1.0)

            peast = threading.Thread(target=self.playeas, args=(Header, altone, Audio_messages, EOM))
            peast.start()
        except:
            dpg.configure_item("statusbar", default_value="Encoder Error", color=(255, 0, 0))
            dpg.configure_item("encoderbroadcastbutton", show=True)
            time.sleep(1)
            dpg.configure_item("statusbar", default_value="Ready", color=(0, 255, 0))
            raise

    def recordaudiomessagevoice(self):
        device_index_input = 0
        for i in range(0, self.paudio.get_device_count()):
            dev = self.paudio.get_device_info_by_index(i)
            if dev['name'] == self.device_name_input:
                device_index_input = dev['index']
                break

        streamin = self.paudio.open(format=pyaudio.paFloat32, channels=1, rate=self.sample_rate, input=True, frames_per_buffer=1024, input_device_index=device_index_input)
        dpg.configure_item("encoderaudiomessagevoicerecordwindow", show=True)

        dpg.configure_item("statusbar", default_value="Recording", color=(255, 255, 0))
        while self.currentiswaitvoiceaudiomessagerecord:
            self.currentvoicemessagesdata.append(streamin.read(1024))
        dpg.configure_item("statusbar", default_value="Stopped Recorded", color=(255, 255, 0))

        self.currentiswaitvoiceaudiomessage = False
        streamin.stop_stream()
        streamin.close()

    def detecttone(self, threshold=0.5, max_attempts=100):
        TYPE_1_FREQS = {853, 960}
        TYPE_2_FREQ = 1050
        target_freqs = TYPE_1_FREQS | {TYPE_2_FREQ}

        device_index_input = 0
        for i in range(self.paudio.get_device_count()):
            dev = self.paudio.get_device_info_by_index(i)
            if dev['name'] == self.device_name_input_EAS:
                device_index_input = dev['index']
                break

        streamin = self.paudio.open(format=pyaudio.paFloat32, channels=1, rate=self.sample_rate, input=True, frames_per_buffer=4096, input_device_index=device_index_input)

        for _ in range(max_attempts):  # Prevent infinite loop
            data = streamin.read(4096)
            data = np.frombuffer(data, dtype=np.float32)

            n = len(data)
            freqs = np.fft.fftfreq(n, d=1 / self.sample_rate)
            spectrum = np.abs(fft.fft(data))

            # Normalize spectrum
            spectrum /= np.max(spectrum)

            detected_freqs = set()
            for target in target_freqs:
                idx = np.argmin(np.abs(freqs - target))  # Find closest frequency bin
                if spectrum[idx] > threshold:
                    detected_freqs.add(target)

            if TYPE_1_FREQS.issubset(detected_freqs):
                return 1
            elif TYPE_2_FREQ in detected_freqs:
                return 2

        return 0

    def playeas(self, Header, altone, Amessages, EOM):
        device_index_output = 0
        for i in range(self.paudio.get_device_count()):
            dev = self.paudio.get_device_info_by_index(i)
            if dev['name'] == self.device_name_output:
                device_index_output = dev['index']
                break

        stream = self.paudio.open(format=pyaudio.paFloat32, channels=1, rate=self.sample_rate, output=True, output_device_index=device_index_output, frames_per_buffer=1024)

        dpg.configure_item("statusbar", default_value="Sending Header", color=(0, 255, 0))
        for i in range(3):
            stream.write(Header.astype(np.float32).tobytes())
            time.sleep(1)

        dpg.configure_item("statusbar", default_value="Sending Tone", color=(0, 255, 0))
        if altone is not None:
            stream.write(altone.astype(np.float32).tobytes())
            time.sleep(1)

        if str(Amessages) != "None":
            if (isinstance(Amessages, str) and Amessages == "waitvoice") or (hasattr(Amessages, 'all') and Amessages.all() is not None):
                if isinstance(Amessages, str):
                    if Amessages == "waitvoice":
                        if dpg.get_value("encodertonetypeinput") == "EAS (853/960 Hz)" or dpg.get_value("encodertonetypeinput") == "NWS (1050 Hz)":
                            altone853 = tonegen(853, 5)
                            altone960 = tonegen(960, 5)
                            h1altone = ((altone853 + altone960) * 0.5)

                            stream.write(h1altone.astype(np.float32).tobytes())
                            if dpg.get_value("encodertonetypeinput") == "NWS (1050 Hz)":
                                stream.write(tonegen(1050, 1).astype(np.float32).tobytes())
                                time.sleep(0.1)
                        while self.currentiswaitvoiceaudiomessage:
                            if dpg.get_value("encodertonetypeinput") == "NWS (1050 Hz)":
                                stream.write(tonegen(1050, 1).astype(np.float32).tobytes())
                            elif dpg.get_value("encodertonetypeinput") == "EAS (853/960 Hz)":
                                altone853 = tonegen(853, 5)
                                altone960 = tonegen(960, 5)
                                h2altone = ((altone853 + altone960) * 0.5)
                                stream.write(h2altone.astype(np.float32).tobytes())
                            else:
                                pass
                        time.sleep(1)
                        dpg.configure_item("statusbar", default_value="Sending Messages", color=(0, 255, 0))
                        for frame in self.currentvoicemessagesdata:
                            stream.write(frame)
                        self.currentvoicemessagesdata = []
                else:
                    dpg.configure_item("statusbar", default_value="Sending Messages", color=(0, 255, 0))
                    stream.write(Amessages.astype(np.float32).tobytes())

        time.sleep(1)

        dpg.configure_item("statusbar", default_value="Sending EOM", color=(0, 255, 0))
        for i in range(3):
            stream.write(EOM.astype(np.float32).tobytes())
            time.sleep(1)

        self.clearlist(None, None)
        self.decoder_is_boardcast = False
        dpg.configure_item("encoderbroadcastbutton", show=True)
        dpg.configure_item("statusbar", default_value="Ready", color=(0, 255, 0))

    def decoder_thread(self):
        first_part = True
        NNNN_count = 0
        dpg.set_value("decoderstatuslabel", "Starting...")
        self.decoder_process = subprocess.Popen(
            ['multimon-ng', '-a', "EAS", "-r", "-q", "-v", "3"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True  # Ensure the output is in text format
        )
        dpg.set_value("decoderstatuslabel", "Running")

        for line in self.decoder_process.stdout:
            output = line.strip()
            self.update_status(output)
            if output.endswith("NNNN"):
                NNNN_count += 1
                if NNNN_count >= 3:
                    time.sleep(2)
                    NNNN_count = 0
                    dpg.set_value("decoderstatuslabel", "Ready")
                    self.latest_part_time_decoder = 0
                    self.delay_detect_tone = 0
                    first_part = True

            if not self.decoder_is_boardcast:
                if output.startswith("EAS (part): "):
                    if first_part:
                        self.latest_part_time_decoder = time.time()
                        first_part = False

                if output.startswith("EAS: ") and output.endswith("-"):
                    self.delay_detect_tone = time.time() - self.latest_part_time_decoder
                    print(self.delay_detect_tone)
                    dpg.set_value("decoderstatuslabel", "EAS Detected")
                    self.decoder_is_boardcast = True
                    broadthread = threading.Thread(target=self.startbroadcast, args=(output,))
                    broadthread.start()

        for line in self.decoder_process.stderr:
            self.update_status(line.strip())

    def stop_decoder(self):
        if self.decoder_process:
            self.decoder_process.terminate()
            self.update_status("stopped")

    def update_status(self, text):
        current_text = dpg.get_value("decoderlog")

        if current_text:
            current_text += "\n"
        current_text += text
        dpg.set_value("decoderlog", current_text)

    def init(self):
        dpg.create_context()
        dpg.create_viewport(title=f'Thesamas ENDEC v{version}', width=1280, height=720)  # set viewport window
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.render_dearpygui_frame()
        # -------------- add code here --------------

        with dpg.window(tag="splash_window", no_move=True, no_close=True, no_title_bar=True, no_resize=True, width=320):
            dpg.add_text("Please wait...")
            dpg.add_text("Initialization...", tag="starting_status")

        dpg.render_dearpygui_frame()
        dpg.set_value("starting_status", "Creating Filter"); dpg.render_dearpygui_frame()

        nyquist = 0.5 * self.sample_rate
        self.filter_b, self.filter_a = signal.butter(4, [500 / nyquist, 2500 / nyquist], btype='band')

        dpg.set_value("starting_status", "Reading file data"); dpg.render_dearpygui_frame()
        with open("events.json", "r") as file:
            self.eventdata = json.load(file)
        with open("Thailand.json", "r") as file:
            self.thailanddata = json.load(file)

        dpg.set_value("starting_status", "Initializing PyAudio"); dpg.render_dearpygui_frame()
        self.paudio = pyaudio.PyAudio()

        dpg.set_value("starting_status", "Creating UI"); dpg.render_dearpygui_frame()

        self.ui = ui(self, version)

        self.ui.menubar()
        self.ui.window()
        event_levels = {'TEST': 0, 'ADV': 1, 'WCH': 2, 'WRN': 3}

        eventlist = []
        for level in self.eventdata.items():
            for code, desc in level[1].items():
                eventlist.append(f"[{findkeybyvalue(event_levels, int(level[0]))}] [{code}] {desc}")

        dpg.configure_item("encoderEventinput", items=eventlist)

        dpg.set_value("starting_status", "Starting Decoder"); dpg.render_dearpygui_frame()

        decoder_thread = threading.Thread(target=self.decoder_thread)
        decoder_thread.start()

        dpg.hide_item("splash_window")

        # -------------------------------------------

        while dpg.is_dearpygui_running():
            self.render()
            dpg.render_dearpygui_frame()

        self.exit()


    def render(self):
        # insert here any code you would like to run in the render loop
        # you can manually stop by using stop_dearpygui() or self.exit()
        #dpg.configure_item("statusspacer", width=dpg.get_viewport_width()-300)
        pass

    def exit(self):
        self.stop_decoder()
        dpg.destroy_context()


app = App()
app.init()