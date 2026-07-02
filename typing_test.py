import time
import random
import sys
import msvcrt
import os

# ── Passages ────────────────────────────────────────────────────────────────

PASSAGES = {
    "easy": [
        "The quick brown fox jumps over the lazy dog. A simple sentence with common words.",
        "A journey of a thousand miles begins with a single step. Keep walking and never stop.",
        "Reading books opens up new worlds. You can travel anywhere without leaving your room.",
    ],
    "medium": [
        "The art of typing is a skill that takes time and practice to develop. Speed comes naturally when accuracy is prioritized first.",
        "Consistency is the key to mastering any new craft. It is better to practice for fifteen minutes every day than to binge once a week.",
        "Water flows effortlessly around obstacles, teaching us that flexibility and persistence can overcome even the hardest stones over time.",
    ],
    "hard": [
        "Proficiency in touch typing requires dedicated practice, muscle memory, and the ability to resist the urge to look at the keyboard while maintaining rhythm and focus.",
        "The philosophical implications of artificial intelligence challenge our understanding of consciousness, demanding rigorous ethical frameworks to ensure alignment with human values.",
        "Quantum mechanics introduces a paradigm where determinism gives way to probabilistic models, fundamentally altering our perception of causality at the subatomic level.",
    ],
}

# ── ANSI colors ──────────────────────────────────────────────────────────────

RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
GREEN   = "\033[32m"
RED     = "\033[31m"
CYAN    = "\033[36m"
YELLOW  = "\033[33m"
WHITE   = "\033[97m"
BG_RED  = "\033[41m"

def clear():
    os.system("cls" if os.name == "nt" else "clear")

# ── Single character reader (Unix) ───────────────────────────────────────────

def getch():
    #Read the frist byte
    ch = msvcrt.getch()
    #if it's a special key prefix
    if ch in (b'\x00',b'\xe0'):
        ch2 = msvcrt.getch()
        #map the window arrow key
        if ch2 == b'H':return "k"
        if ch2 == b'p':return "j"
        return"\x1b"
    try:
        return ch.decode("utf-8")
    except UnicodeDecodeError:
        return ""

# ── Rendering ────────────────────────────────────────────────────────────────

def render(passage: str, typed: list[str], cursor: int,
           wpm: float, accuracy: float, elapsed: float, phase: str):
    clear()

    # Header
    print(f"\n  {BOLD}{CYAN}Typing Speed Test{RESET}\n")
    print(f"  {DIM}{'─' * 60}{RESET}\n")

    # Stats bar
    wpm_str      = f"{int(wpm):>4}"
    acc_str      = f"{int(accuracy):>3}%"
    time_str     = f"{elapsed:>5.1f}s"
    print(f"  {BOLD}WPM{RESET} {CYAN}{wpm_str}{RESET}   "
          f"{BOLD}Accuracy{RESET} {WHITE}{acc_str}{RESET}   "
          f"{BOLD}Time{RESET} {WHITE}{time_str}{RESET}\n")
    print(f"  {DIM}{'─' * 60}{RESET}\n")

    # Passage with per-character coloring (wrap at 60 chars)
    line_len = 60
    words = passage
    display = ""
    for i, ch in enumerate(passage):
        if i < len(typed):
            if typed[i] == ch:
                display += f"{GREEN}{ch}{RESET}"
            else:
                # Show what was typed over the expected char in red
                display += f"{BG_RED}{WHITE}{ch}{RESET}"
        elif i == cursor:
            display += f"{BOLD}{YELLOW}{ch}{RESET}"   # cursor position
        else:
            display += f"{DIM}{ch}{RESET}"

    # Word-wrap the colored string (count visible chars, not ANSI codes)
    lines = []
    current_line = ""
    visible_count = 0
    i = 0
    raw = list(display)
    while i < len(raw):
        if raw[i] == "\033":
            # ANSI escape — consume until 'm'
            seq = ""
            while i < len(raw) and raw[i] != "m":
                seq += raw[i]
                i += 1
            seq += "m"
            i += 1
            current_line += seq
        else:
            current_line += raw[i]
            visible_count += 1
            i += 1
            if visible_count >= line_len and raw[i - 1] == " ":
                lines.append(current_line)
                current_line = ""
                visible_count = 0

    if current_line:
        lines.append(current_line)

    for line in lines:
        print(f"  {line}")

    print()

    # Progress bar
    progress = cursor / len(passage) if passage else 0
    bar_width = 60
    filled = int(bar_width * progress)
    bar = f"{CYAN}{'█' * filled}{DIM}{'░' * (bar_width - filled)}{RESET}"
    print(f"  {bar}  {int(progress * 100)}%\n")

    if phase == "ready":
        print(f"  {DIM}Start typing to begin  |  Backspace to correct  |  Ctrl+C to quit{RESET}\n")
    elif phase == "typing":
        print(f"  {DIM}Backspace to correct  |  Ctrl+C to quit{RESET}\n")

# ── Results screen ───────────────────────────────────────────────────────────

LABELS = [(100, "Expert"), (70, "Fast"), (50, "Skilled"), (30, "Average"), (0, "Novice")]

def performance_label(wpm: float) -> str:
    for threshold, label in LABELS:
        if wpm >= threshold:
            return label
    return "Novice"

def show_results(wpm: float, accuracy: float, elapsed: float):
    clear()
    label = performance_label(wpm)
    print(f"\n  {BOLD}{CYAN}─── Results ───────────────────────────────────{RESET}\n")
    print(f"  {BOLD}Performance{RESET}  {CYAN}{BOLD}{label}{RESET}")
    print()
    print(f"  {BOLD}Speed      {RESET}  {WHITE}{int(wpm)} WPM{RESET}")
    print(f"  {BOLD}Accuracy   {RESET}  {WHITE}{int(accuracy)}%{RESET}")
    print(f"  {BOLD}Time       {RESET}  {WHITE}{elapsed:.1f}s{RESET}")
    print()
    print(f"  {DIM}{'─' * 47}{RESET}")
    print(f"\n  Press {BOLD}R{RESET} to retry  |  {BOLD}N{RESET} for new passage  |  {BOLD}Q{RESET} to quit\n")

# ── Core typing loop ─────────────────────────────────────────────────────────

def run_test(passage: str):
    typed: list[str] = []
    correct_count  = 0
    incorrect_count = 0
    start_time: float | None = None
    elapsed = 0.0

    render(passage, typed, 0, 0, 100, 0, "ready")

    while True:
        ch = getch()

        # Ctrl+C → quit
        if ch in ("\x03", "\x04"):
            clear()
            sys.exit(0)

        cursor = len(typed)

        # Start timer on first real keypress
        if start_time is None and ch != "\x7f":
            start_time = time.time()

        if ch == "\x7f":  # Backspace
            if typed:
                last = typed.pop()
                expected = passage[len(typed)]
                if last == expected:
                    correct_count   = max(0, correct_count - 1)
                else:
                    incorrect_count = max(0, incorrect_count - 1)

        elif len(typed) < len(passage):
            expected = passage[len(typed)]
            typed.append(ch)
            if ch == expected:
                correct_count += 1
            else:
                incorrect_count += 1

        # Elapsed time
        elapsed = time.time() - start_time if start_time else 0.0

        # WPM & accuracy
        total = correct_count + incorrect_count
        minutes = elapsed / 60 if elapsed > 0 else 1e-9
        wpm = (correct_count / 5) / minutes
        accuracy = (correct_count / total * 100) if total > 0 else 100.0

        cursor = len(typed)
        phase = "typing" if start_time else "ready"
        render(passage, typed, cursor, wpm, accuracy, elapsed, phase)

        # Finished
        if len(typed) == len(passage):
            return wpm, accuracy, elapsed

# ── Difficulty selector ──────────────────────────────────────────────────────

def choose_difficulty() -> str:
    options = list(PASSAGES.keys())
    selected = 1  # default: medium

    while True:
        clear()
        print(f"\n  {BOLD}{CYAN}Typing Speed Test{RESET}\n")
        print(f"  Choose difficulty:\n")
        for i, diff in enumerate(options):
            marker = f"{CYAN}>{RESET}" if i == selected else " "
            print(f"  {marker} {diff.capitalize()}")
        print(f"\n  {DIM}Arrow keys / j k to navigate  |  Enter to select{RESET}\n")

        ch = getch()
        if ch in ("k", "\x1b"):  # up (also catches ESC for arrow key prefix)
            selected = (selected - 1) % len(options)
        elif ch == "j":           # down
            selected = (selected + 1) % len(options)
        elif ch == "\r":          # Enter
            return options[selected]
        elif ch in ("\x03", "\x04"):
            clear()
            sys.exit(0)

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    difficulty = choose_difficulty()
    passage = random.choice(PASSAGES[difficulty])

    while True:
        wpm, accuracy, elapsed = run_test(passage)
        show_results(wpm, accuracy, elapsed)

        ch = getch().lower()
        if ch == "r":
            continue                                   # same passage
        elif ch == "n":
            pool = [p for p in PASSAGES[difficulty] if p != passage]
            passage = random.choice(pool or PASSAGES[difficulty])
        elif ch in ("q", "\x03", "\x04"):
            clear()
            break

if __name__ == "__main__":
    main()