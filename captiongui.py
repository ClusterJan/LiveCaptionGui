import tkinter
import tkinter as tk
import threading
import queue
import time


class CaptionGUI:
    """
    Creates the window for displaying the captions.
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Live Caption GUI")
        self.root.geometry("600x300")
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.frame = tk.Frame(self.root, bg="black")
        self.frame.grid(sticky=tk.NSEW)
        # self.frame.pack(fill=tk.BOTH, expand=True)
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)

        self.start_btn = tkinter.Button(self.frame, text="Start",
                                        fg="black", bg="black",
                                        command=lambda: self.start_robots())
        self.start_btn.config(width=10)
        self.start_btn.grid(row=0, column=1)

        self.label_caption_1_queue = queue.Queue()
        self.label_caption_1_text = tk.StringVar()
        self.label_caption_1_text.set("Here could be your caption.")

        self.label_caption_1 = tk.Label(self.frame, font=("Helvetica", 30),
                                        bg="black", fg="white", wraplength=800, justify=tk.CENTER,
                                        textvariable=self.label_caption_1_text)

        self.label_caption_1_robot = Robot("robot_one", self.label_caption_1_queue)
        self.label_caption_1_updater = LabelUpdater("updater_one", self.label_caption_1_queue, self.root,
                                                    self.label_caption_1_text)
        self.label_caption_1_updater.start()

        self.label_caption_1.grid(row=1, column=1)

        self.root.mainloop()

    def start_robots(self):
        self.label_caption_1_robot.start()


class Robot(threading.Thread):
    def __init__(self, name: str, label_queue: queue.Queue):
        super().__init__(name=name)
        self.daemon = True
        self.label_queue = label_queue
        self.caption_file = open("/Users/janvonaschwege/PycharmProjects/live-translation/captions.txt", "r")

    def run(self) -> None:
        while True:
            next_lines = self.caption_file.readline().split("~^~")
            if next_lines[0]:
                # Only look at the last n lines, assuming the previous are stable
                n = 3
                line = "\n".join(next_lines[-n:])
                self.label_queue.put(line)
            time.sleep(0.5)


class LabelUpdater(threading.Thread):
    def __init__(self, name: str, label_queue: queue.Queue, root_app: tkinter.Tk, variable: tkinter.Variable):
        super().__init__(name=name)
        self.daemon = True
        self.label_queue = label_queue
        self.root_app = root_app
        self.variable = variable

    def run(self) -> None:
        # run forever
        while True:
            # wait a second please
            time.sleep(3)
            # try:
            #    text = self.label_queue.get(block=False)
            # except queue.Empty:
            #    continue
            # self.variable.set(self.label_queue.get())
            # consume all the queue and keep only the last message
            last_msg = None
            while True:
                try:
                    msg = self.label_queue.get(block=False)
                except queue.Empty:
                    break
                last_msg = msg
                self.label_queue.task_done()
            if last_msg:
                self.variable.set(last_msg)
