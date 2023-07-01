import itertools
import logging
import threading
import time
import tkinter as tk
from tkinter import messagebox

from google.cloud import mediatranslation as media
from six.moves import queue

import whisper
import torch
from tempfile import NamedTemporaryFile
import wave

from microphone import MicrophoneStream

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

# Translation parameters
SOURCE_LANGUAGE = "it-IT"
TARGET_LANGUAGE = "en-US"

# GUI parameters
CAPTION_UPDATE_INTERVAL = 0.1  # seconds
TIMEOUT_AFTER_FINAL_CAPTION = 2  # seconds

SpeechEventType = media.StreamingTranslateSpeechResponse.SpeechEventType


def write_to_wav(audio_content, wav_file):
    wf = wave.open(wav_file, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(2)  # assuming audio_content is int16
    wf.setframerate(RATE)
    wf.writeframes(audio_content)
    wf.close()
    return wav_file


class CaptionGUI:
    """
    Creates the window for displaying the captions.
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Live Caption GUI")
        self.root.geometry("1500x400")
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.frame = tk.Frame(self.root, bg="black")
        self.frame.grid(sticky=tk.NSEW)
        # self.frame.pack(fill=tk.BOTH, expand=True)
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)

        self.start_btn = tk.Button(self.frame, text="Start",
                                   fg="black", bg="black",
                                   command=lambda: self.start_robots())
        self.start_btn.config(width=5)
        self.start_btn.grid(row=0, column=0)

        self.stop_btn = tk.Button(self.frame, text="Stop",
                                  fg="black", bg="black",
                                  command=lambda: self.stop_robots())
        self.stop_btn.config(width=5)
        self.stop_btn.grid(row=0, column=2)

        self.label_caption_1_queue = queue.Queue()  # Queue for the caption label: (translation, is_final)
        self.label_caption_1_text = tk.StringVar()
        self.label_caption_1_text.set("System is ready.\nPress Start to begin.")

        self.label_caption_1 = tk.Label(self.frame, font=("Helvetica", 80),
                                        bg="black", fg="white", wraplength=1400, justify=tk.CENTER,
                                        textvariable=self.label_caption_1_text)

        self.label_caption_1_robot = Robot("robot_one", self.label_caption_1_queue)
        self.label_caption_1_updater = LabelUpdater("updater_one", self.label_caption_1_queue, self.root,
                                                    self.label_caption_1_text)
        self.label_caption_1_updater.start()

        self.label_caption_1.grid(row=1, column=0, columnspan=3)

        self.root.mainloop()

    def start_robots(self):
        print("Robot started")
        self.label_caption_1_robot.start()

    def stop_robots(self):
        print("Robot stopped")
        self.label_caption_1_robot.stop()

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.label_caption_1_robot.stop()
            self.root.destroy()
            self.root.quit()


class Robot(threading.Thread):
    def __init__(self, name: str, label_queue: queue.Queue):
        super().__init__(name=name)
        self.daemon = True
        self.running = False
        self.label_queue = label_queue
        self.audio_model = whisper.load_model('tiny')

    def start(self) -> None:
        self.running = True
        logging.info(f"Starting {self.name} thread.")
        super().start()

    def stop(self) -> None:
        self.running = False
        self.label_queue.put(("...", True))

    def run(self) -> None:
        while self.running:
            self._translation_loop()

    def _translation_loop(self):
        with MicrophoneStream(RATE, CHUNK) as stream:
            audio_generator = stream.generator()
            while self.running:
                audio_content = next(audio_generator)
                # Convert the audio_content to a temporary wav file to be fed to whisper
                with NamedTemporaryFile(suffix=".wav", delete=True) as temp_wav:
                    wav_file = write_to_wav(audio_content,
                                            temp_wav.name)  # You have to implement write_to_wav function to convert raw audio to wav
                    # Use Whisper ASR for transcription
                    result = self.audio_model.transcribe(wav_file, fp16=torch.cuda.is_available())
                    translation = result['text'].strip()
                    self.label_queue.put((translation, False))  # Partial Translation
                    if not translation:  # If there is no translation, treat it as the end of an utterance
                        self.label_queue.put((translation, True))
                        return 0

    def _print_translation_loop(self, responses):
        """
        Iterates through server responses and add them to the label queue.

        The responses passed is a generator that will block until a response
        is provided by the server.
        """
        translation = ""
        for response in responses:
            # Once the transcription settles, the response contains the
            # END_OF_SINGLE_UTTERANCE event.
            if response.speech_event_type == SpeechEventType.END_OF_SINGLE_UTTERANCE:
                self.label_queue.put((translation, True))
                return 0

            # Display the translation for the segments detected in the audio
            # stream.
            result = response.result
            translation = result.text_translation_result.translation
            self.label_queue.put((translation, False))  # Partial Translation


class LabelUpdater(threading.Thread):
    def __init__(self, name: str, label_queue: queue.Queue, root_app: tk.Tk, variable: tk.Variable):
        super().__init__(name=name)
        self.daemon = True
        self.label_queue = label_queue
        self.root_app = root_app
        self.variable = variable

    def run(self) -> None:
        # run forever
        while True:
            # wait a second please
            time.sleep(CAPTION_UPDATE_INTERVAL)

            last_msg = None
            while True:
                try:
                    msg, is_final = self.label_queue.get(block=False)
                except queue.Empty:
                    break

                if is_final:
                    self.variable.set(msg)
                    self.label_queue.task_done()
                    time.sleep(TIMEOUT_AFTER_FINAL_CAPTION)
                    break
                else:
                    last_msg = msg
                    self.label_queue.task_done()
            if last_msg:
                self.variable.set(last_msg)
