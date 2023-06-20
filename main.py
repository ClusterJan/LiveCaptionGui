from pynput import keyboard
from captiongui import CaptionGUI


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    gui = CaptionGUI()

    with keyboard.GlobalHotKeys({
        '<shift>+A': gui.start_robots,
        '<shift>+D': gui.stop_robots
    }) as h:
        h.join()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
