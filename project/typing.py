import sys

try:
    import curses
    from curses import wrapper
    USE_CURSES = True
except ModuleNotFoundError:
    curses = None
    wrapper = None
    USE_CURSES = False
import time
import random

# keep a session pool of available texts to avoid repeats
_available_texts = None

def start_screen(stdscr):
    stdscr.clear()
    stdscr.addstr("Welcome To your speed Typing test!")
    stdscr.addstr("\n press any key to start!")
    stdscr.refresh()
    stdscr.getkey()


def display_text(stdscr, target, current, wpm=0):
    stdscr.addstr(target)
    stdscr.addstr(1,0,f"WPM: {wpm}")

    for i,char in enumerate(current):
        correct_char = target[i]
        color = curses.color_pair(1)
        if char != correct_char:
            color = curses.color_pair(2)

        stdscr.addstr(0,i,char,color)
        
def load_text():
    global _available_texts
    if not _available_texts:
        with open("text.txt","r") as f:
            _available_texts = [line.strip() for line in f if line.strip()]
    choice = random.choice(_available_texts)
    _available_texts.remove(choice)
    return choice
    
def wpm_test(stdscr):
    target_text = load_text()
    current_text = []
    wpm =0
    start_time = time.time()
    stdscr.nodelay(True)
    
    while True:
        
        time_elapsed = max(time.time() - start_time, 1)
        wpm = round((len(current_text)/(time_elapsed/60))/5)
        
        stdscr.clear()
        display_text(stdscr, target_text,current_text,wpm)
        
        if "".join(current_text) == target_text:
            stdscr.nodelay(False)
            break
        
        try:
            key = stdscr.getkey()
        except Exception:
            continue

        # Exit on ESC (ASCII 27)
        if key == "\x1b":
            break

        # Handle backspace keys
        if key in ("KEY_BACKSPACE", "\b", "\x7f"):
            if len(current_text) > 0:
                current_text.pop()
        # Append printable characters (only up to target length)
        elif len(current_text) < len(target_text):
            current_text.append(key)
                
def main(stdscr):
    curses.start_color()
    curses.init_pair(1,curses.COLOR_GREEN,curses.COLOR_BLACK)
    curses.init_pair(2,curses.COLOR_RED,curses.COLOR_BLACK)
    curses.init_pair(3,curses.COLOR_BLUE,curses.COLOR_BLACK)

    start_screen(stdscr)
    while True:
        wpm_test(stdscr)
        stdscr.addstr(2,0,"You completed the text! Press any key is you would like to continue...")
        key = stdscr.getkey()
        
        if key == "\x1b":
            break
        
        
        

def console_start_screen():
    print("Welcome To your speed Typing test!")
    input("Press Enter to start...")

def console_wpm_test():
    target_text = load_text()
    print("\nType the following text exactly and press Enter:\n")
    print(target_text)
    start_time = time.time()
    typed = input('\nYour input: ')
    elapsed = max(time.time() - start_time, 1)
    correct_chars = sum(1 for a,b in zip(typed, target_text) if a==b)
    wpm = round((len(typed)/(elapsed/60))/5)
    print(f"\nElapsed: {elapsed:.2f}s | WPM: {wpm} | Correct chars: {correct_chars}/{len(target_text)}\n")

def console_main():
    console_start_screen()
    while True:
        console_wpm_test()
        cont = input("You completed the text! Press Enter to continue, or type 'q' then Enter to quit: ")
        if cont.strip().lower() == 'q':
            break


if USE_CURSES and wrapper is not None:
    wrapper(main)
else:
    console_main()

