# main.py
import random
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle

# base clear color (will be covered by gradient)
Window.clearcolor = (1, 1, 1, 1)

# ---------- Gradient background ----------
class GradientBackground(BoxLayout):
    def __init__(self, top_color=(0.99,0.99,0.97), bottom_color=(0.88,0.93,1.0), steps=60, **kwargs):
        super().__init__(**kwargs)
        self.top_color = top_color
        self.bottom_color = bottom_color
        self.steps = max(6, int(steps))
        # draw many thin rectangles to simulate vertical gradient
        with self.canvas:
            self._colors = []
            self._rects = []
            for i in range(self.steps):
                c = Color(1, 1, 1, 1)
                r = Rectangle(pos=(0, 0), size=(0, 0))
                self._colors.append(c)
                self._rects.append(r)
        self.bind(size=self._update, pos=self._update)
        Window.bind(size=self._update)
        self._update()

    def _lerp(self, a, b, t):
        return a + (b - a) * t

    def _update(self, *l):
        w, h = Window.size
        step_h = float(h) / self.steps
        for i, rect in enumerate(self._rects):
            t = i / max(1, self.steps - 1)
            r = self._lerp(self.top_color[0], self.bottom_color[0], t)
            g = self._lerp(self.top_color[1], self.bottom_color[1], t)
            b = self._lerp(self.top_color[2], self.bottom_color[2], t)
            # set color instruction (Color object stored same index)
            try:
                self._colors[i].rgba = (r, g, b, 1)
            except Exception:
                pass
            rect.pos = (0, i * step_h)
            rect.size = (w, step_h + 1)

# ---------- Game widget ----------
class TicTacToeGame(BoxLayout):
    def __init__(self, vs_ai=True, exit_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 14
        self.spacing = 10

        self.vs_ai = vs_ai
        self.exit_callback = exit_callback

        self.current_player = "X"
        self.board = [["" for _ in range(3)] for _ in range(3)]

        # Status
        self.status = Label(text=f"Player {self.current_player}'s turn",
                            font_size='20sp', size_hint=(1, 0.12),
                            color=(0.06,0.06,0.06,1))
        self.add_widget(self.status)

        # Board grid
        self.grid = GridLayout(cols=3, rows=3, spacing=6, size_hint=(1, 0.76))
        self.buttons = [[None]*3 for _ in range(3)]
        for r in range(3):
            for c in range(3):
                btn = Button(text="", font_size='38sp',
                             background_normal='', background_color=(1,1,1,1))
                btn.bind(on_release=lambda inst, rr=r, cc=c: self.on_cell(rr, cc))
                self.buttons[r][c] = btn
                self.grid.add_widget(btn)
        self.add_widget(self.grid)

        # Controls: Restart + Back
        controls = GridLayout(cols=2, size_hint=(1, 0.12), spacing=8)
        restart_btn = Button(text="Restart", font_size='16sp', background_normal='',
                             background_color=(0.22, 0.6, 0.86, 1), color=(1,1,1,1))
        restart_btn.bind(on_release=self.reset_game)
        back_btn = Button(text="Back", font_size='16sp', background_normal='',
                          background_color=(0.86, 0.22, 0.3, 1), color=(1,1,1,1))
        back_btn.bind(on_release=lambda *a: self.exit_callback())
        controls.add_widget(restart_btn)
        controls.add_widget(back_btn)
        self.add_widget(controls)

    def on_cell(self, row, col):
        # ignore if occupied or game over
        if self.board[row][col] != "" or self.get_winner() or self.is_board_full():
            return

        # in friend mode, symbol comes from current_player
        if self.vs_ai:
            # player is always X; AI is O
            self.play_move(row, col, "X")
            if self.get_winner():
                self.end_game_popup("Player X wins!")
                return
            if self.is_board_full():
                self.end_game_popup("It's a tie!")
                return
            # AI move
            self.ai_move_improved()
        else:
            # friend mode: alternate turns
            symbol = self.current_player
            self.play_move(row, col, symbol)
            if self.get_winner():
                self.end_game_popup(f"Player {symbol} wins!")
                return
            if self.is_board_full():
                self.end_game_popup("It's a tie!")
                return
            # switch turn
            self.current_player = "O" if self.current_player == "X" else "X"
            self.status.text = f"Player {self.current_player}'s turn"

    def play_move(self, row, col, symbol):
        self.board[row][col] = symbol
        btn = self.buttons[row][col]
        btn.text = symbol
        if symbol == "X":
            btn.color = (0.04, 0.4, 0.9, 1)  # blue
        else:
            btn.color = (0.9, 0.08, 0.08, 1)  # red
        btn.background_color = (0.98, 0.98, 1, 1)

    # Improved AI heuristic (strong but not full minimax)
    def ai_move_improved(self):
        if self.get_winner() or self.is_board_full():
            return

        # 1) Win if possible
        move = self.find_winning_move("O")
        # 2) Block opponent
        if not move:
            move = self.find_winning_move("X")
        # 3) Take center
        if not move and self.board[1][1] == "":
            move = (1,1)
        # 4) Take opposite corner if opponent in corner
        if not move:
            move = self.take_opposite_corner()
        # 5) Take empty corner
        if not move:
            corners = [(0,0),(0,2),(2,0),(2,2)]
            random.shuffle(corners)
            for c in corners:
                if self.board[c[0]][c[1]] == "":
                    move = c
                    break
        # 6) Take any side
        if not move:
            sides = [(0,1),(1,0),(1,2),(2,1)]
            random.shuffle(sides)
            for s in sides:
                if self.board[s[0]][s[1]] == "":
                    move = s
                    break
        # fallback
        if not move:
            empties = [(r,c) for r in range(3) for c in range(3) if self.board[r][c] == ""]
            if empties:
                move = random.choice(empties)

        if move:
            r, c = move
            self.play_move(r, c, "O")

            if self.get_winner():
                self.end_game_popup("Player O wins!")
                return
            if self.is_board_full():
                self.end_game_popup("It's a tie!")
                return
            # back to player
            self.current_player = "X"
            self.status.text = f"Player {self.current_player}'s turn"

    def find_winning_move(self, symbol):
        for r in range(3):
            for c in range(3):
                if self.board[r][c] == "":
                    self.board[r][c] = symbol
                    winner = self.get_winner()
                    self.board[r][c] = ""
                    if winner == symbol:
                        return (r, c)
        return None

    def take_opposite_corner(self):
        opp_corners = [((0,0),(2,2)), ((0,2),(2,0)), ((2,0),(0,2)), ((2,2),(0,0))]
        for oc, myc in opp_corners:
            if self.board[oc[0]][oc[1]] == "X" and self.board[myc[0]][myc[1]] == "":
                return myc
        return None

    # game helpers
    def get_winner(self):
        b = self.board
        for i in range(3):
            if b[i][0] == b[i][1] == b[i][2] != "":
                return b[i][0]
            if b[0][i] == b[1][i] == b[2][i] != "":
                return b[0][i]
        if b[0][0] == b[1][1] == b[2][2] != "":
            return b[0][0]
        if b[0][2] == b[1][1] == b[2][0] != "":
            return b[0][2]
        return None

    def is_board_full(self):
        return all(all(cell != "" for cell in row) for row in self.board)

    # reset & popup
    def reset_game(self, *args):
        self.board = [["" for _ in range(3)] for _ in range(3)]
        for r in range(3):
            for c in range(3):
                btn = self.buttons[r][c]
                btn.text = ""
                btn.background_color = (1,1,1,1)
                btn.color = (0,0,0,1)
        self.current_player = "X"
        self.status.text = f"Player {self.current_player}'s turn"

    def end_game_popup(self, message):
        layout = BoxLayout(orientation='vertical', spacing=10, padding=12)
        label = Label(text=message, font_size='18sp', color=(0.06,0.06,0.06,1))
        layout.add_widget(label)

        btns = BoxLayout(size_hint=(1, 0.45), spacing=10)
        play_again = Button(text="Play Again", background_normal='',
                            background_color=(0.22,0.6,0.86,1), color=(1,1,1,1))
        back_btn = Button(text="Back", background_normal='',
                          background_color=(0.86,0.22,0.3,1), color=(1,1,1,1))
        popup = Popup(title="Game Over", content=layout, size_hint=(0.8, 0.36))
        play_again.bind(on_release=lambda *a: (self.reset_game(), popup.dismiss()))
        back_btn.bind(on_release=lambda *a: (popup.dismiss(), self.exit_callback()))
        btns.add_widget(play_again)
        btns.add_widget(back_btn)
        layout.add_widget(btns)
        popup.open()

# ---------- Mode selector (with Exit) ----------
class ModeSelector(BoxLayout):
    def __init__(self, start_callback, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 22
        self.spacing = 14

        title = Label(text="Tic Tac Toe", font_size='36sp', size_hint=(1, 0.22), color=(0.06,0.06,0.06,1))
        subtitle = Label(text="Choose Mode", font_size='16sp', size_hint=(1, 0.12), color=(0.33,0.33,0.33,1))
        self.add_widget(title)
        self.add_widget(subtitle)

        btn_box = BoxLayout(orientation='vertical', spacing=12, size_hint=(1, 0.6))
        ai_btn = Button(text="Play vs AI", font_size='18sp', size_hint=(1, None), height=58,
                        background_normal='', background_color=(0.22,0.6,0.86,1), color=(1,1,1,1))
        friend_btn = Button(text="Play with Friend", font_size='18sp', size_hint=(1, None), height=58,
                            background_normal='', background_color=(0.95,0.82,0.3,1), color=(0.06,0.06,0.06,1))
        exit_btn = Button(text="Exit", font_size='18sp', size_hint=(1, None), height=58,
                          background_normal='', background_color=(0.86,0.22,0.3,1), color=(1,1,1,1))

        ai_btn.bind(on_release=lambda *a: start_callback(True))
        friend_btn.bind(on_release=lambda *a: start_callback(False))
        exit_btn.bind(on_release=lambda *a: App.get_running_app().stop())

        btn_box.add_widget(ai_btn)
        btn_box.add_widget(friend_btn)
        btn_box.add_widget(exit_btn)

        tip = Label(text="AI is improved: it will try win/block/center/corner moves.", font_size='13sp',
                    size_hint=(1, 0.12), color=(0.33,0.33,0.33,1))

        self.add_widget(btn_box)
        self.add_widget(tip)

# ---------- App ----------
class TicTacToeApp(App):
    def build(self):
        root = BoxLayout()
        gradient = GradientBackground(top_color=(0.99,0.99,0.97), bottom_color=(0.88,0.93,1.0), steps=80)
        root.add_widget(gradient)
        self.layer = BoxLayout()
        root.add_widget(self.layer)
        self.show_mode_selector()
        return root

    def show_mode_selector(self):
        self.layer.clear_widgets()
        selector = ModeSelector(self.start_game)
        self.layer.add_widget(selector)

    def start_game(self, vs_ai):
        self.layer.clear_widgets()
        game = TicTacToeGame(vs_ai=vs_ai, exit_callback=self.show_mode_selector)
        self.layer.add_widget(game)

if __name__ == '__main__':
    TicTacToeApp().run()
