# THsEAmaS (Beta)
Thai Emergency Specific Area Message Alert System based on EAS

![image](https://github.com/user-attachments/assets/e5e93a78-6a37-438d-a21c-2c3fc6359e5d)

# Setup
* This software is developed in windows so I can show step only in windows (Linux later)

1. Install Python (3.10+) and download this repo.

2. Install package  
```sh
pip install dearpygui numpy pyttsx3 PyAudio soundfile scipy
```

3. changing settings in file `standalone.py`
```py
self.sender = "THsEAmaS" # change your call sign or name of station
# use "python -m sounddevice" to scan device name
self.device_name_input = "" # microphone input
self.device_name_input_EAS = "CABLE Output (VB-Audio Virtual " # microphone input from receiver
self.device_name_output = "CABLE Input (VB-Audio Virtual C" # output to mixer or processor
```
use `python -m sounddevice` for find your device

4.Changing microphone input from receiver for `multimon-ng` (If you are using Windows 11, you can follow my steps. However, I'm not sure if my steps will work for Windows 10 or 7 or older version.) 
* 1. Goto **Settings** -> **System** -> **Sound**.
  ![image](https://github.com/user-attachments/assets/d1243ac8-55e0-4d14-ad58-70ef0dc4a387)
  2. Then scroll down to **Volume mixer** and click into it.
  ![image](https://github.com/user-attachments/assets/88bb841c-3c43-48ab-ba56-6bc7cd2cb07a)
  3. Find `multimon-ng.exe` then select then goto Input device and choose your microphone input from receiver
  ![image](https://github.com/user-attachments/assets/a0fc73b8-784c-442e-b739-677db90a650e)

5. Launch this code by click the `standalone.py` or use command
```sh
python3 standalone.py
```

# Demo
Sorry! I will demo later.

# Development History
* This software will update when incident occurred or I want to update.

### V1: First Version 

Code: [Gist](https://gist.github.com/damp11113/f5207eb45a05f02f359da59c006aa5dc)
Post: [X](https://x.com/damp11113/status/1709970281669046629)
Test: [Video](https://www.youtube.com/watch?v=VU4LiQCGYz4)

Developed in 4/10/2023 (after Siam Paragon Shooting)

### V1.1-1.5: Ui Update
Developed in 1/11/2023

### V1.6: Decoder Update (First Release)
Developed in 28/3/2025 (after Earthquake)
