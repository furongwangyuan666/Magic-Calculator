import tkinter as tk
import webbrowser
import subprocess
import threading
import time
import ctypes
import ctypes.wintypes as wintypes
import keyboard

user32 = ctypes.windll.user32
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def copy_to_clipboard(text):
    proc = subprocess.Popen("clip", stdin=subprocess.PIPE, shell=True, encoding="utf-16le")
    proc.communicate(input=text)


def find_browser_window():
    result = []
    keywords = ["Chrome", "Edge", "Firefox", "浏览器", "豆包", "doubao"]

    def callback(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                if any(kw.lower() in buf.value.lower() for kw in keywords):
                    result.append(hwnd)
        return True

    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return result[0] if result else None


def get_window_title(hwnd):
    length = user32.GetWindowTextLengthW(hwnd)
    if length > 0:
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value
    return ""


def find_browser_window():
    result = []
    keywords = ["Chrome", "Edge", "Firefox", "浏览器", "豆包", "doubao"]

    def callback(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            title = get_window_title(hwnd)
            if title and any(kw.lower() in title.lower() for kw in keywords):
                result.append(hwnd)
        return True

    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return result[0] if result else None


def wait_for_doubao_loaded(timeout=20):
    """轮询浏览器窗口标题，检测豆包页面是否加载完成"""
    hwnd = find_browser_window()
    if not hwnd:
        time.sleep(3)
        return None

    old_title = get_window_title(hwnd)
    deadline = time.time() + timeout

    while time.time() < deadline:
        title = get_window_title(hwnd)
        if title != old_title:
            lower = title.lower()
            if "doubao" in lower or "豆包" in lower:
                time.sleep(2)
                return hwnd
        time.sleep(0.3)

    return hwnd


def auto_paste_and_send(question):
    try:
        hwnd = wait_for_doubao_loaded(timeout=20)
        if hwnd:
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.5)
        copy_to_clipboard(question)
        time.sleep(0.3)
        keyboard.press_and_release("ctrl+v")
        time.sleep(0.3)
        keyboard.press_and_release("enter")
    except Exception:
        pass


class MagicCalculator:
    BG = "#1a1a2e"
    DISPLAY_BG = "#16213e"
    BTN_NUM_BG = "#2a2a4a"
    BTN_NUM_HOVER = "#3a3a5a"
    BTN_OP_BG = "#4338ca"
    BTN_OP_HOVER = "#5b4cdb"
    BTN_EQ_BG = "#7c3aed"
    BTN_EQ_HOVER = "#9061f5"
    BTN_CLEAR_BG = "#991b1b"
    BTN_CLEAR_HOVER = "#b91c1c"
    BTN_FUNC_BG = "#1e293b"
    BTN_FUNC_HOVER = "#334155"
    TEXT = "#ffffff"
    TEXT_DIM = "#94a3b8"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("神奇计算器")
        self.root.geometry("380x560")
        self.root.resizable(False, False)
        self.root.configure(bg=self.BG)

        self.current = "0"
        self.expression = ""
        self.just_evaluated = False

        self._build_ui()
        self._bind_keys()

    def _build_ui(self):
        tk.Label(
            self.root, text="AI 神奇计算器", font=("Microsoft YaHei UI", 11),
            bg=self.BG, fg=self.TEXT_DIM
        ).pack(pady=(16, 8))

        disp_frame = tk.Frame(self.root, bg=self.DISPLAY_BG, bd=0, highlightthickness=1,
                              highlightbackground="#2a2a4a")
        disp_frame.pack(padx=20, fill="x")

        self.formula_label = tk.Label(
            disp_frame, text="", font=("Consolas", 13),
            bg=self.DISPLAY_BG, fg="#64748b", anchor="e", padx=16, pady=2
        )
        self.formula_label.pack(fill="x", pady=(14, 0))

        self.result_label = tk.Label(
            disp_frame, text="0", font=("Consolas", 36, "bold"),
            bg=self.DISPLAY_BG, fg=self.TEXT, anchor="e", padx=16, pady=2
        )
        self.result_label.pack(fill="x", pady=(0, 18))

        btn_frame = tk.Frame(self.root, bg=self.BG)
        btn_frame.pack(padx=20, pady=(16, 8), fill="both", expand=True)

        for i in range(5):
            btn_frame.rowconfigure(i, weight=1)
        for j in range(4):
            btn_frame.columnconfigure(j, weight=1)

        buttons = [
            ("AC", 0, 0, "clear"), ("(", 0, 1, "func"), (")", 0, 2, "func"), ("/", 0, 3, "op"),
            ("7", 1, 0, "num"), ("8", 1, 1, "num"), ("9", 1, 2, "num"), ("*", 1, 3, "op"),
            ("4", 2, 0, "num"), ("5", 2, 1, "num"), ("6", 2, 2, "num"), ("-", 2, 3, "op"),
            ("1", 3, 0, "num"), ("2", 3, 1, "num"), ("3", 3, 2, "num"), ("+", 3, 3, "op"),
            ("0", 4, 0, "num"), (".", 4, 1, "num"), ("⌫", 4, 2, "func"), ("=", 4, 3, "eq"),
        ]

        for (text, r, c, kind) in buttons:
            colspan = 2 if text == "0" else 1
            bg, hover = self._btn_colors(kind)
            btn = tk.Button(
                btn_frame, text=text, font=("Microsoft YaHei UI", 16, "bold"),
                bg=bg, fg=self.TEXT, activebackground=hover, activeforeground=self.TEXT,
                bd=0, relief="flat", cursor="hand2",
                command=lambda t=text, k=kind: self._on_click(t, k)
            )
            btn.grid(row=r, column=c, columnspan=colspan, sticky="nsew", padx=4, pady=4)
            btn.bind("<Enter>", lambda e, b=btn, h=hover: b.config(bg=h))
            btn.bind("<Leave>", lambda e, b=btn, k=kind: b.config(bg=self._btn_colors(k)[0]))

        tk.Label(
            self.root, text='点击 = 唤起豆包 AI 计算',
            font=("Microsoft YaHei UI", 9), bg=self.BG, fg="#4a4a6a"
        ).pack(pady=(0, 12))

    def _btn_colors(self, kind):
        return {
            "num":   (self.BTN_NUM_BG,   self.BTN_NUM_HOVER),
            "op":    (self.BTN_OP_BG,    self.BTN_OP_HOVER),
            "eq":    (self.BTN_EQ_BG,    self.BTN_EQ_HOVER),
            "clear": (self.BTN_CLEAR_BG, self.BTN_CLEAR_HOVER),
            "func":  (self.BTN_FUNC_BG,  self.BTN_FUNC_HOVER),
        }[kind]

    def _on_click(self, text, kind):
        if kind == "num":
            self._input_num(text)
        elif kind == "op":
            self._input_op(text)
        elif kind == "func":
            if text == "AC":
                self._clear()
            elif text == "⌫":
                self._backspace()
            else:
                self._input_func(text)
        elif kind == "eq":
            self._ask_doubao()

    def _input_num(self, n):
        if self.just_evaluated:
            self.current = "0." if n == "." else n
            self.expression = ""
            self.just_evaluated = False
        elif n == ".":
            if "." not in self.current:
                self.current += "."
        else:
            self.current = n if self.current == "0" else self.current + n
        self._update_display()

    def _input_op(self, op):
        if self.just_evaluated:
            self.expression = self.current
            self.just_evaluated = False
        elif self.expression and self.expression[-1] not in "+-*/":
            self.expression += self.current
        else:
            self.expression = self.expression or self.current
        self.expression += op
        self.current = "0"
        self._update_display()

    def _input_func(self, f):
        if self.just_evaluated:
            self.current = "0"
            self.expression = ""
            self.just_evaluated = False
        if self.current == "0":
            self.current = ""
        self.current += f
        self._update_display()

    def _clear(self):
        self.current = "0"
        self.expression = ""
        self.just_evaluated = False
        self._update_display()

    def _backspace(self):
        if len(self.current) > 1:
            self.current = self.current[:-1]
        else:
            self.current = "0"
        self._update_display()

    def _ask_doubao(self):
        full = self.expression + self.current
        if not full or full == "0":
            return
        display = full.replace("*", "×").replace("/", "÷")
        question = "请帮我计算：" + display

        copy_to_clipboard(question)
        webbrowser.open("https://www.doubao.com/chat/")

        t = threading.Thread(target=auto_paste_and_send, args=(question,), daemon=True)
        t.start()

        self.just_evaluated = True

    def _update_display(self):
        self.result_label.config(text=self.current)
        disp_expr = self.expression.replace("*", "×").replace("/", "÷")
        self.formula_label.config(text=disp_expr)

    def _bind_keys(self):
        self.root.bind("<Key>", self._on_key)

    def _on_key(self, event):
        k = event.keysym
        ch = event.char
        if ch in "0123456789":
            self._input_num(ch)
        elif ch == ".":
            self._input_num(".")
        elif ch in "+-*/":
            self._input_op(ch)
        elif ch in "()":
            self._input_func(ch)
        elif ch == "=" or k == "Return":
            self._ask_doubao()
        elif k == "Escape":
            self._clear()
        elif k == "BackSpace":
            self._backspace()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    MagicCalculator().run()
