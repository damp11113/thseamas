import os
from tkinter import filedialog
import dearpygui.dearpygui as dpg

def limit_string_in_line(text, limit):
    lines = text.split('\n')
    new_lines = []

    for line in lines:
        words = line.split()
        new_line = ''

        for word in words:
            if len(new_line) + len(word) <= limit:
                new_line += word + ' '
            else:
                new_lines.append(new_line.strip())
                new_line = word + ' '

        if new_line:
            new_lines.append(new_line.strip())

    return '\n'.join(new_lines)

class ui:
    def __init__(self, app, version):
        self.app = app
        self.version = version

    def stopvoicerecord(self, sender, data):
        dpg.configure_item("encoderaudiomessagevoicerecordwindow", show=False)
        self.app.currentiswaitvoiceaudiomessagerecord = False

    def setmessagetottseditpath(self, sender, data):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")], title="Please select text file")
        if file_path:
            with open(file_path, "r") as file:
                dpg.configure_item("encoderaudiomessagetypettsmessageinput", default_value=file.read())
                file.close()
            dpg.configure_item("encodereditaudiomessagestatustext", default_value=os.path.basename(file_path))
            self.app.ttsfromtext = True

    def setwavaudiomessagepath(self):
        file_path = filedialog.askopenfilename(filetypes=[("Wav audio file", "*.wav")], title="Please select wav file")
        self.app.currentwavaudiomessagepath = file_path
        dpg.configure_item("encodereditaudiomessagestatustext", default_value=os.path.basename(file_path))

    def setmessagesetedmessagetts(self, sender, data):
        if self.app.ttsfromtext:
            self.app.ttsfromtext = False
        else:
            dpg.configure_item("encodereditaudiomessagestatustext", default_value="TTS Text OK")

        dpg.configure_item("encoderaudiomessagetypettsmessagewindow", show=False)

    def addlocationtolist(self, sender, data):
        prov = dpg.get_value("encoderProvincialinput")
        area = dpg.get_value("encoderAreainput")

        if prov == "":
            return
        if area == "":
            return

        if prov in self.app.eventlist:
            dpg.configure_item("messageexistpopup", default_value=f"{prov} already exists in the list.")
            dpg.configure_item("existpopup", show=True)
        else:
            self.app.eventlist.update({prov: area})
            with dpg.table_row(parent="Eventzonelist", tag=f"Eventzonelistrow{self.app.currentitemcountlist}"):
                dpg.add_text(prov)
                dpg.add_text(area)
            self.app.currentitemcountlist += 1

    def showeditaudiomessagebutton(self, sender, data):
        dpg.configure_item("encodereditaudiomessagestatustext", default_value="Not Set")
        self.app.ttsfromtext = False
        self.app.audiomessagetype = dpg.get_value(sender)
        if self.app.audiomessagetype in ["TTS", "WAV"]:
            dpg.configure_item("encodereditaudiomessagebutton", show=True)
            dpg.configure_item("encodereditaudiomessagestatustext", show=True)
        else:
            dpg.configure_item("encodereditaudiomessagebutton", show=False)
            dpg.configure_item("encodereditaudiomessagestatustext", show=False)

    def openeditaudiomessage(self, sender, data):
        if self.app.audiomessagetype == "TTS":
            dpg.configure_item("encoderaudiomessagetypettsmessagewindow", show=True)
        elif self.app.audiomessagetype == "WAV":
            self.setwavaudiomessagepath()

    def window(self):
        with dpg.window(label="Encoder", width=400, height=620, tag="Encoderwindow", no_close=True):
            with dpg.menu_bar():
                with dpg.menu(label="Presets"):
                    dpg.add_menu_item(label="Load")
                    dpg.add_menu_item(label="Save")
                    dpg.add_menu_item(label="Clear")

            dpg.add_text("Broadcast settings")
            with dpg.child_window(height=175):
                dpg.add_combo(["[PEP] National Public Warning",
                               "[CIV] Civil authorities",
                               "[WXR] National Weather Service",
                               "[EAS] EAS Participant"
                               ], label="Originator", tag="encoderORGinput")
                dpg.add_combo([], label="Event", tag="encoderEventinput")
                dpg.add_text("Event duration (HH:MM:SS) (second isn't require)")
                dpg.add_time_picker(hour24=True, tag="encodertimepurgeinput", default_value={'hour': 0, 'min': 0, 'sec': 0})
                dpg.add_combo(["No Audio", "Voice (from mic)", "TTS", "WAV"], label="Audio Messages", tag="encoderaudiomessagetypeinput", callback=self.showeditaudiomessagebutton, default_value="Voice (from mic)")
                dpg.add_button(label="Edit Audio Messages", tag="encodereditaudiomessagebutton", show=False, callback=self.openeditaudiomessage)
                dpg.add_text("Not Set", tag="encodereditaudiomessagestatustext", show=False, pos=(155, 123))
                dpg.add_combo(["No Tone", "EAS (853/960 Hz)", "NWS (1050 Hz)"], label="Attention Tone", tag="encodertonetypeinput", default_value="EAS (853/960 Hz)")
            dpg.add_text("Broadcast Location")
            with dpg.child_window(height=100):
                dpg.add_combo(list(self.app.thailanddata.keys()), label="Provincial", tag="encoderProvincialinput")
                dpg.add_combo(
                    self.app.area,
                    label="Area", tag="encoderAreainput", default_value="All")
                dpg.add_button(label="Add Location", callback=self.addlocationtolist)
            with dpg.child_window(height=200):
                dpg.add_text("Location")
                dpg.add_button(label="Clear All", callback=lambda: dpg.configure_item("clearlistwarningpopup", show=True))
                with dpg.table(header_row=True, tag="Eventzonelist"):
                    dpg.add_table_column(label="Provincial")
                    dpg.add_table_column(label="Area")

            dpg.add_button(label="Broadcast", callback=lambda: dpg.configure_item("broadcastwarningpopup", show=True), tag="encoderbroadcastbutton")

        with dpg.window(label="Warning!", modal=True, show=False, tag="broadcastwarningpopup", no_resize=True, no_move=True):
            dpg.add_text("False Alarm Warning!")
            dpg.add_spacer()
            warning = """
                A false alarm in an emergency alert system refers to the issuance of an alert when there isn't an actual emergency or threat present. It's essentially an erroneous or mistaken alarm that triggers the dissemination of emergency notifications, causing unnecessary panic or confusion among the public. False alarms can occur due to technical glitches, human error, or misinterpretation of data, and they can lead to a loss of trust in the reliability of the alert system. Authorities work to minimize false alarms by improving technology, refining protocols, and ensuring accuracy in the detection and dissemination of emergency alerts.
            """
            dpg.add_text(limit_string_in_line(warning, 75))
            dpg.add_spacer()
            dpg.add_text(limit_string_in_line("This is a notification from NBTC regarding a false alarm. There is NO ongoing emergency situation at this time.", 75))
            dpg.add_text(limit_string_in_line("Please remain calm and carry on with your regular activities. We apologize for any inconvenience caused by this false alarm. Your safety remains our utmost priority.", 75))
            dpg.add_text(limit_string_in_line("For any further updates or inquiries, please stay tuned to local news channels or contact 1200.", 75))
            dpg.add_text("Thank you for your cooperation.")
            dpg.add_spacer()
            dpg.add_button(label="Not sure", callback=lambda: dpg.configure_item("broadcastwarningpopup", show=False))
            dpg.add_button(label="I have read and accept the broadcast risk warning.", callback=lambda: self.app.startbroadcast())
            dpg.add_spacer()
            dpg.add_text("Thesamas is first Prototype EAS in Thailand and maybe have the errors or bugs!")

        with dpg.window(label="Decoder", width=400, height=520, tag="Decoderwindow", no_close=True):
            dpg.add_text("Status: Unknown", tag="decoderstatuslabel")
            dpg.add_input_text(multiline=True, tag="decoderlog", height=-1, width=-1, readonly=True)

        with dpg.window(label="Exist", modal=True, show=False, tag="existpopup", no_resize=True, no_move=True):
            dpg.add_text("", tag="messageexistpopup")
            dpg.add_spacer()
            dpg.add_button(label="OK", callback=lambda: dpg.configure_item("existpopup", show=False))

        with dpg.window(label="Warning", modal=True, show=False, tag="clearlistwarningpopup", no_resize=True, no_move=True):
            dpg.add_text("This is clear all list in table. Please check the data.")
            dpg.add_spacer()
            dpg.add_button(label="OK", callback=self.app.clearlist)
            dpg.add_button(label="cancel", callback=lambda: dpg.configure_item("clearlistwarningpopup", show=False))

        with dpg.window(label="Edit TTS Messages", modal=True, show=False, tag="encoderaudiomessagetypettsmessagewindow", width=750, height=430):
            dpg.add_button(label="Import", callback=self.setmessagetottseditpath)
            dpg.add_text("Messages to speak")
            dpg.add_input_text(multiline=True, tag="encoderaudiomessagetypettsmessageinput", height=320, width=730)
            dpg.add_spacer()
            dpg.add_button(label="OK", callback=self.setmessagesetedmessagetts)

        with dpg.window(label="Speak Here!", modal=True, show=False, tag="encoderaudiomessagevoicerecordwindow"):
            dpg.add_text("click ok for 'End Voice' for start transmit voice")
            dpg.add_spacer()
            dpg.add_button(label="End Voice", callback=self.stopvoicerecord)

        with dpg.window(label="Thesamas About", tag="aboutwindow", show=False, no_resize=True):
            #dpg.add_image("app_logo")
            #dpg.add_spacer()
            dpg.add_text("Thesamas (Thai emergency specific area message alert system)")
            dpg.add_spacer()
            dpg.add_text(f"Thesamas ENDEC v{self.version}")
            dpg.add_spacer()

            desc = """
            Thesamas is first Prototype EAS (emergency alert system) in Thailand using SAME encode (Specific Area Message Encoding) 
            """

            dpg.add_text(limit_string_in_line(desc, 75))

            dpg.add_spacer(height=20)
            dpg.add_text(f"Copyright (C) 2023-2024 ThaiSDR All rights reserved. (GPLv3)")

        with dpg.window(label="Thesamas Docs", tag="docswindow", show=False, no_resize=True):
            with dpg.tab_bar():
                with dpg.tab(label="V1"):
                    desc = """
                        code: ZCZC-ORG-EEE-APP066+TTTT-JJJHHMM-LLLLLLLL-
                        -------------------------------------------------------------
                        ZCZC = Start
                        ORG = Originator code EAS CIV WXR PEP
                        EEE = Event code
                        AAGGPP066 = A = Area (0 = All)
                                  PP = Provincial (05 = Phatthaya, 00 = All country)
                                  066 = Country Code (If use in country use 066 for default)
                        TTTT = Purge time (HHMM) (0000 = Testing) HH = Hour
                                                                  MM = Minute
                        JJJHHMM = JJJ = Julian day
                                  HH = Hour
                                  MM = Minute
                        LLLLLLLL = Station Callsign aka Sender
                        -------------------------------------------------------------
                    """

                    dpg.add_text(limit_string_in_line(desc, 75))
                with dpg.tab(label="V2"):
                    desc = """
                        ___________Can add more zone
                        __________________||
                        __________________\/
                        code: ZCZC-ORG-EEE-AAPP066+TTTT-JJJHHMM-LLLLLLLL-
                        -------------------------------------------------------------
                        ZCZC = Start
                        ORG = Originator code EAS CIV WXR PEP
                        EEE = Event code
                        AAGGPP066 = AA = Area (00 = All)
                                  PP = Provincial (05 = Phatthaya, 00 = All country)
                                  066 = Country Code (If use in country use 066 for default)
                        TTTT = Purge time (HHMM) (0000 = Testing) HH = Hour
                                                                  MM = Minute
                        JJJHHMM = JJJ = Julian day
                                  HH = Hour
                                  MM = Minute
                        LLLLLLLL = Station Callsign aka Sender
                        -------------------------------------------------------------
                    """

                    dpg.add_text(limit_string_in_line(desc, 75))

    def menubar(self):
        with dpg.viewport_menu_bar():
            with dpg.menu(label="File"):
            #     dpg.add_text("-----Preset-----")
            #     dpg.add_menu_item(label="Load")
            #     dpg.add_menu_item(label="Save")
            #     dpg.add_menu_item(label="Clear")
            #     dpg.add_text("----------------")
                  dpg.add_menu_item(label="Exit", callback=lambda: self.app.exit())
            with dpg.menu(label="Settings"):
                dpg.add_menu_item(label="Config")#, callback=lambda: dpg.configure_item("configwindow", show=True))
                dpg.add_spacer()
                dpg.add_menu_item(label="StyleEditor", callback=dpg.show_style_editor)
            with dpg.menu(label="Help"):
                dpg.add_menu_item(label="Docs", callback=lambda: dpg.configure_item("docswindow", show=True))
                dpg.add_menu_item(label="About", callback=lambda: dpg.configure_item("aboutwindow", show=True))
            #dpg.add_spacer(width=dpg.get_viewport_width()-300, tag="statusspacer")

            dpg.add_text("Ready", tag="statusbar", color=(0, 255, 0), pos=(dpg.get_viewport_width()-100, 0))