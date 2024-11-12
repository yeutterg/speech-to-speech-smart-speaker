# Speech-to-Speech Smart Speaker

This is the Python code for a smart speaker (like the Amazon Echo or Google Home) that is built atop [OpenAI's Realtime API](https://platform.openai.com/docs/guides/realtime). This speech-to-speech API is more conversational and lower latency than traditional voice assistants, such as Alexa.

Follow the [build log on YouTube](https://www.youtube.com/playlist?list=PLboszRf3aO5aD2V_da5jIyB33Sp1MpEe3).

This is an open-source project, and all improvements are welcome! Please submit pull requests. Let's build the future of ambient intelligence together.

## BOM

For a basic working smart speaker that is easy to set up, you can use the following components:

| Component | Description |
| --- | --- | 
| [Raspberry Pi 5](https://www.adafruit.com/product/5812) | The brains of the operation |
| [microSD Card](https://www.amazon.com/dp/B0B7NTY2S6) | Flash storage for the Raspberry Pi |
| [Adafruit Voice Bonnet](https://www.adafruit.com/product/4757) | A sound card for the Raspberry Pi with microphones and audio outputs |
| [3 Watt Speaker](https://www.adafruit.com/product/3351) | Storage for the Raspberry Pi's operating system and data |

## Setup

### Raspberry Pi Setup

If using a Raspberry Pi, you have many options to flash and set up the OS. Here is just one way:

1. Install the [Raspberry Pi Imager](https://www.raspberrypi.com/software/) on your computer
2. Mount a microSD card you want to flash
3. Open the Imager. On the first page, select your device and microSD card target. Choose Raspberry Pi OS Lite (64-bit) if you don't need a GUI and just want to SSH in
4. Edit the settings: 
* General tab: Set a custom hostname, username and password, Wi-Fi, and locale
* Services: Enable SSH
5. Flash the SD card with the image, then eject after completion
6. Insert the microSD card into the Raspberry Pi, then power the device up
7. Go into your router's DHCP table or use a sniffer to find the device's IP address
8. Attempt to SSH into the device. Open your terminal, then type ```ssh username@ip```, where username is the username you set in step 4, and IP is the address you found in step 7
9. If the SSH connection was successful, type the password you set in step 4
10. Update the system: ```sudo apt update && sudo apt upgrade```
11. Install Python tools: ```sudo apt-get install python3-pip && sudo apt install --upgrade python-setuptools```

### Adafruit Voice Bonnet Setup

If you are using the [Adafruit Voice Bonnet](https://www.adafruit.com/product/4757) for audio input and output, here's how to set it up:

1. [Install Blinka](https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi) to enable the CircuitPython libraries on your Raspberry Pi
2. [Install the Voicecard software](https://learn.adafruit.com/adafruit-voice-bonnet/audio-setup), then run a speaker and microphone test
3. Install the Python audio packages: 

```bash
sudo apt-get install libportaudio2 portaudio19-dev
pip3 install pyaudio
```

4. To test the whether the Python libraries work with the speaker and microphone:
* Create a new file: ```touch audiotest.py```
* Open the file: ```vi audiotest.py```
* Press ```i```, then paste [this code snippet](https://arc.net/l/quote/hhdfvhiv)
* Press ```esc```, then ```:wq```
* Run ```python3 audiotest.py```, follow the prompts, and record some audio
* Run ```aplay myrecording.wav``` to play back the recording

### Project Setup

1. Clone this repository into a directory on your Raspberry Pi
2. Go to [platform.openai.com](https://platform.openai.com/), create an account and add $5-$10 credit (if you haven't already), then [create a new API secret key](https://platform.openai.com/api-keys) and copy it
3. Make a copy of .env.sample and rename it to .env.local
4. Paste your new API key into .env.local under ```OPENAI_API_KEY=""```
5. Install the Python dependencies: ```pip3 install -r requirements.txt```
6. Run the project: ```python3 main.py```
