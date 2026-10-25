import random
import tkinter as tk
from tkinter import messagebox, ttk

# Definición de categorías del Yahtzee clásico
CATEGORIES = [
    "Unos",
    "Dos",
    "Tres",
    "Cuatros",
    "Cincos",
    "Seises",
    "Tres de un tipo",
    "Cuatro de un tipo",
    "Full House",
    "Escala Corta",
    "Escala Larga",
    "Yahtzee",
    "Suerte",
]


def score_category(dice, category):
    """Calcula la puntuación de un conjunto de 5 dados para una categoría dada."""
    counts = {i: dice.count(i) for i in range(1, 7)}
    total = sum(dice)

    if category == "Unos":
        return counts.get(1, 0) * 1
    if category == "Dos":
        return counts.get(2, 0) * 2
    if category == "Tres":
        return counts.get(3, 0) * 3
    if category == "Cuatros":
        return counts.get(4, 0) * 4
    if category == "Cincos":
        return counts.get(5, 0) * 5
    if category == "Seises":
        return counts.get(6, 0) * 6

    if category == "Tres de un tipo":
        return total if any(c >= 3 for c in counts.values()) else 0
    if category == "Cuatro de un tipo":
        return total if any(c >= 4 for c in counts.values()) else 0
    if category == "Full House":
        has_3 = 3 in counts.values()
        has_2 = 2 in counts.values()
        has_5 = 5 in counts.values()  # Yahtzee cuenta como Full House válido en algunas reglas
        return 25 if (has_3 and has_2) or has_5 else 0
    if category == "Escala Corta":
        unique = set(dice)
        straights = [{1, 2, 3, 4}, {2, 3, 4, 5}, {3, 4, 5, 6}]
        return 30 if any(s.issubset(unique) for s in straights) else 0
    if category == "Escala Larga":
        unique = set(dice)
        return 40 if unique == {1, 2, 3, 4, 5} or unique == {2, 3, 4, 5, 6} else 0
    if category == "Yahtzee":
        return 50 if any(c == 5 for c in counts.values()) else 0
    if category == "Suerte":
        return total
    return 0


def monte_carlo_optimize(current_dice, held_mask, available_categories, simulations=300):
    """Método de Monte Carlo: Simula tiradas aleatorias para los dados no retenidos

    y evalúa qué categoría reporta el puntaje esperado más alto.
    """
    unheld_count = 5 - sum(held_mask)
    if unheld_count == 0 or not available_categories:
        # Si no hay dados que lanzar, evaluamos directamente las categorías
        best_cat = max(
            available_categories,
            key=lambda cat: score_category(current_dice, cat),
            default=None,
        )
        return best_cat, score_category(current_dice, best_cat) if best_cat else 0

    category_expected_scores = {cat: 0.0 for cat in available_categories}

    for _ in range(simulations):
        # Simular los dados que faltan por lanzar
        simulated_unheld = [random.randint(1, 6) for _ in range(unheld_count)]
        full_simulated_dice = [
            current_dice[i] if held_mask[i] else simulated_unheld.pop(0)
            for i in range(5)
        ]

        for cat in available_categories:
            category_expected_scores[cat] += score_category(
                full_simulated_dice, cat
            )

    # Promediar los resultados de la simulación
    for cat in category_expected_scores:
        category_expected_scores[cat] /= simulations

    best_category = max(category_expected_scores, key=category_expected_scores.get)
    return best_category, category_expected_scores[best_category]


class YahtzeeApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Yahtzee Clásico - 2 Jugadores con Monte Carlo")
        self.root.geometry("900x650")
        self.root.configure(bg="#f4f6f9")

        # Estado del juego
        self.current_player = 0  # 0 o 1
        self.players = ["Jugador 1", "Jugador 2"]
        self.scores = [
            {cat: None for cat in CATEGORIES},
            {cat: None for cat in CATEGORIES},
        ]
        self.rolls_left = 3
        self.dice = [1, 1, 1, 1, 1]
        self.held = [False, False, False, False, False]
        self.rounds_completed = 0

        self.create_widgets()
        self.start_new_turn()

    def create_widgets(self):
        # Panel Superior: Estado de turno
        top_frame = tk.Frame(self.root, bg="#2c3e50", pady=10)
        top_frame.pack(fill=tk.X)

        self.turn_label = tk.Label(
            top_frame,
            text="",
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#2c3e50",
        )
        self.turn_label.pack()

        self.rolls_label = tk.Label(
            top_frame,
            text="",
            font=("Arial", 12),
            fg="#ecf0f1",
            bg="#2c3e50",
        )
        self.rolls_label.pack()

        # Panel Central: Dados y controles
        center_frame = tk.Frame(self.root, bg="#f4f6f9", pady=20)
        center_frame.pack()

        dice_frame = tk.Frame(center_frame, bg="#f4f6f9")
        dice_frame.pack(pady=10)

        self.dice_buttons = []
        for i in range(5):
            btn = tk.Button(
                dice_frame,
                text="1",
                font=("Arial", 18, "bold"),
                width=4,
                height=2,
                bg="white",
                command=lambda idx=i: self.toggle_hold(idx),
            )
            btn.grid(row=0, column=i, padx=8)
            self.dice_buttons.append(btn)

        btn_action_frame = tk.Frame(center_frame, bg="#f4f6f9")
        btn_action_frame.pack(pady=10)

        self.roll_btn = tk.Button(
            btn_action_frame,
            text="Lanzar Dados",
            font=("Arial", 12, "bold"),
            bg="#27ae60",
            fg="white",
            padx=10,
            pady=5,
            command=self.roll_dice,
        )
        self.roll_btn.pack(side=tk.LEFT, padx=10)

        self.mc_btn = tk.Button(
            btn_action_frame,
            text="Sugerencia IA (Monte Carlo)",
            font=("Arial", 12, "bold"),
            bg="#2980b9",
            fg="white",
            padx=10,
            pady=5,
            command=self.run_monte_carlo_advice,
        )
        self.mc_btn.pack(side=tk.LEFT, padx=10)

        # Panel Inferior: Tabla de puntuaciones
        score_frame = tk.Frame(self.root, bg="#f4f6f9", padx=20)
        score_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Treeview para mostrar las tarjetas de puntuación de ambos jugadores
        self.tree = ttk.Treeview(
            score_frame, columns=("Category", "P1", "P2"), show="headings", height=13
        )
        self.tree.heading("Category", text="Categoría")
        self.tree.heading("P1", text="Jugador 1")
        self.tree.heading("P2", text="Jugador 2")
        self.tree.column("Category", width=200, anchor="w")
        self.tree.column("P1", width=120, anchor="center")
        self.tree.column("P2", width=120, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind("<Double-1>", self.select_score_category)

        # Actualizar tabla inicial
        self.update_score_table()

    def update_score_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for cat in CATEGORIES:
            p1_val = (
                str(self.scores[0][cat])
                if self.scores[0][cat] is not None
                else "-"
            )
            p2_val = (
                str(self.scores[1][cat])
                if self.scores[1][cat] is not None
                else "-"
            )
            self.tree.insert("", tk.END, values=(cat, p1_val, p2_val))

    def start_new_turn(self):
        self.rolls_left = 3
        self.held = [False, False, False, False, False]
        self.dice = [random.randint(1, 6) for _ in range(5)]
        self.update_ui_state()

    def update_ui_state(self):
        self.turn_label.config(
            text=f"Turno de: {self.players[self.current_player]}"
        )
        self.rolls_label.config(text=f"Tiradas restantes: {self.rolls_left}")

        for i in range(5):
            state_text = f"[{self.dice[i]}]" if self.held[i] else f" {self.dice[i]} "
            bg_color = "#d5dbdb" if self.held[i] else "white"
            self.dice_buttons[i].config(text=state_text, bg=bg_color)

        if self.rolls_left > 0:
            self.roll_btn.config(state=tk.NORMAL)
        else:
            self.roll_btn.config(state=tk.DISABLED)

    def toggle_hold(self, index):
        if self.rolls_left < 3:  # Solo se puede bloquear después del primer lanzamiento
            self.held[index] = not self.held[index]
            self.update_ui_state()

    def roll_dice(self):
        if self.rolls_left > 0:
            for i in range(5):
                if not self.held[i]:
                    self.dice[i] = random.randint(1, 6)
            self.rolls_left -= 1
            self.update_ui_state()

    def run_monte_carlo_advice(self):
        # Obtener categorías aún no usadas por el jugador actual
        available = [
            cat
            for cat, val in self.scores[self.current_player].items()
            if val is None
        ]
        if not available:
            messagebox.showinfo(
                "Monte Carlo", "No quedan categorías disponibles."
            )
            return

        best_cat, expected_score = monte_carlo_optimize(
            self.dice, self.held, available, simulations=500
        )
        messagebox.showinfo(
            "Asistente Monte Carlo",
            f"Basado en 500 simulaciones estocásticas:\n\n"
            f"• Mejor categoría sugerida: {best_cat}\n"
            f"• Puntuación esperada estimada: {expected_score:.1f} pts",
        )

    def select_score_category(self, event):
        # Permitir al usuario hacer doble clic en una categoría de la tabla para anotar
        if self.rolls_left == 3:
            messagebox.showwarning(
                "Aviso", "Debes lanzar los dados al menos una vez antes de anotar."
            )
            return

        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        item = self.tree.item(item_id)
        category = item["values"][0]

        if self.scores[self.current_player][category] is not None:
            messagebox.showwarning("Aviso", "¡Esta categoría ya está ocupada!")
            return

        # Calcular puntos para la categoría seleccionada
        points = score_category(self.dice, category)
        self.scores[self.current_player][category] = points

        self.update_score_table()
        self.check_game_over()

        # Cambiar de turno
        self.current_player = 1 - self.current_player
        self.start_new_turn()

    def check_game_over(self):
        # Verificar si ambos jugadores han llenado todas sus categorías
        p1_done = all(v is not None for v in self.scores[0].values())
        p2_done = all(v is not None for v in self.scores[1].values())

        if p1_done and p2_done:
            p1_total = sum(v for v in self.scores[0].values())
            p2_total = sum(v for v in self.scores[1].values())

            winner_msg = f"¡Juego Terminado!\n\nJugador 1: {p1_total} pts\nJugador 2: {p2_total} pts\n\n"
            if p1_total > p2_total:
                winner_msg += "¡Ganador: Jugador 1!"
            elif p2_total > p1_total:
                winner_msg += "¡Ganador: Jugador 2!"
            else:
                winner_msg += "¡Empate!"

            messagebox.showinfo("Fin del Juego", winner_msg)
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = YahtzeeApp(root)
    root.mainloop()