import random
import streamlit as st

# --- Configuración de la página ---
st.set_page_config(page_title="Juego de Póker en Streamlit", page_icon="🃏", layout="centered")

# --- Clases y Lógica del Póker (Five-Card Draw) ---
SUITS = ['♠️', '♥️', '♦️', '♣️']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
RANK_VALUES = {r: i for i, r in enumerate(RANKS, start=2)}


class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.value = RANK_VALUES[rank]

    def __repr__(self):
        return f"{self.rank}{self.suit}"


def create_deck():
    deck = [Card(r, s) for s in SUITS for r in RANKS]
    random.shuffle(deck)
    return deck


def evaluate_hand(hand):
    """
    Evalúa una mano de 5 cartas y devuelve una tupla (puntuación, desempate)
    para comparar manos de forma precisa.
    """
    values = sorted([c.value for c in hand], reverse=True)
    suits = [c.suit for c in hand]

    is_flush = len(set(suits)) == 1

    # Comprobar escalera
    is_straight = False
    if len(set(values)) == 5:
        if values[0] - values[4] == 4:
            is_straight = True
        # Escalera especial A-2-3-4-5 (As bajo)
        elif values == [14, 5, 4, 3, 2]:
            values = [5, 4, 3, 2, 1]
            is_straight = True

    from collections import Counter
    counts = Counter(values)
    sorted_counts = sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse=True)

    frequencies = [freq for val, freq in sorted_counts]
    unique_values = [val for val, freq in sorted_counts]

    # Jerarquía de manos de póker:
    if is_flush and is_straight:
        return (8, values)  # Escalera de color
    elif frequencies == [4, 1]:
        return (7, unique_values)  # Póker
    elif frequencies == [3, 2]:
        return (6, unique_values)  # Full House
    elif is_flush:
        return (5, values)  # Color
    elif is_straight:
        return (4, values)  # Escalera
    elif frequencies == [3, 1, 1]:
        return (3, unique_values)  # Trío
    elif frequencies == [2, 2, 1]:
        return (2, unique_values)  # Doble pareja
    elif frequencies == [2, 1, 1, 1]:
        return (1, unique_values)  # Pareja
    else:
        return (0, values)  # Carta alta


HAND_NAMES = {
    8: "Escalera de Color 🌟",
    7: "Póker 🔥",
    6: "Full House 🏠",
    5: "Color (Flush) 🎨",
    4: "Escalera (Straight) 📈",
    3: "Trío 🎯",
    2: "Doble Pareja ✌️",
    1: "Pareja 👥",
    0: "Carta Alta 🎴"
}

# --- Inicialización del Estado de Sesión ---
if 'game_state' not in st.session_state:
    st.session_state.game_state = 'start'
    st.session_state.player_chips = 1000
    st.session_state.ai_chips = 1000
    st.session_state.pot = 0
    st.session_state.deck = []
    st.session_state.player_hand = []
    st.session_state.ai_hand = []

st.title("🃏 Sala de Póker - Five-Card Draw")
st.markdown("Juega al póker clásico contra la inteligencia artificial. ¡Gestiona tus fichas y gana el pozo!")

# --- Marcador Superior ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Tus Fichas", f"${st.session_state.player_chips}")
with col2:
    st.metric("Pozo Actual", f"${st.session_state.pot}")
with col3:
    st.metric("Fichas de la IA", f"${st.session_state.ai_chips}")

st.markdown("---")

# --- Fases del Juego ---

if st.session_state.game_state == 'start':
    st.info("Presiona el botón para repartir las cartas (Apuesta inicial ciega: $50 cada uno).")
    if st.button("Repartir Cartas 🎲", type="primary"):
        if st.session_state.player_chips < 50 or st.session_state.ai_chips < 50:
            st.warning("¡Un jugador no tiene suficientes fichas! Reiniciando bankroll a $1000.")
            st.session_state.player_chips = 1000
            st.session_state.ai_chips = 1000

        st.session_state.player_chips -= 50
        st.session_state.ai_chips -= 50
        st.session_state.pot = 100

        deck = create_deck()
        st.session_state.player_hand = [deck.pop() for _ in range(5)]
        st.session_state.ai_hand = [deck.pop() for _ in range(5)]
        st.session_state.deck = deck

        st.session_state.game_state = 'discard'
        st.rerun()

elif st.session_state.game_state == 'discard':
    st.subheader("Tu Mano Actual:")

    selected_indices = []
    cols = st.columns(5)
    for i, card in enumerate(st.session_state.player_hand):
        with cols[i]:
            st.markdown(f"### {card}")
            if st.checkbox("Descartar", key=f"discard_{i}"):
                selected_indices.append(i)

    st.markdown(
        "Selecciona las casillas de las cartas que deseas **descartar y cambiar** por nuevas, luego presiona el botón.")

    if st.button("Cambiar Cartas 🔄"):
        # Reemplazar cartas del jugador
        for idx in sorted(selected_indices, reverse=True):
            if st.session_state.deck:
                st.session_state.player_hand[idx] = st.session_state.deck.pop()

        # Turno de la IA: evalúa si tiene parejas para conservar o cambia cartas bajas
        ai_hand = st.session_state.ai_hand
        ai_values = [c.value for c in ai_hand]
        from collections import Counter

        counts = Counter(ai_values)
        keep_indices = [i for i, c in enumerate(ai_hand) if counts[c.value] > 1 or c.value >= 11]
        discard_ai = [i for i in range(5) if i not in keep_indices]
        if len(discard_ai) > 3:
            discard_ai = discard_ai[:3]

        for idx in discard_ai:
            if st.session_state.deck:
                st.session_state.ai_hand[idx] = st.session_state.deck.pop()

        st.session_state.game_state = 'showdown'
        st.rerun()

elif st.session_state.game_state == 'showdown':
    st.subheader("Resultados del Enfrentamiento (Showdown)")

    col_p, col_a = st.columns(2)

    with col_p:
        st.markdown("**Tus Cartas:**")
        st.write(" ".join([str(c) for c in st.session_state.player_hand]))
        p_score = evaluate_hand(st.session_state.player_hand)
        st.success(f"Tu jugada: **{HAND_NAMES[p_score[0]]}**")

    with col_a:
        st.markdown("**Cartas de la IA:**")
        st.write(" ".join([str(c) for c in st.session_state.ai_hand]))
        ai_score = evaluate_hand(st.session_state.ai_hand)
        st.warning(f"Jugada de la IA: **{HAND_NAMES[ai_score[0]]}**")

    pot = st.session_state.pot
    if p_score > ai_score:
        st.balloons()
        st.success(f"🎉 ¡Felicidades! Has ganado el pozo de **${pot}**.")
        st.session_state.player_chips += pot
    elif p_score < ai_score:
        st.error(f"🤖 La IA ha ganado el pozo de **${pot}**.")
        st.session_state.ai_chips += pot
    else:
        st.info(f"🤝 ¡Empate! El pozo de **${pot}** se divide en partes iguales.")
        st.session_state.player_chips += pot // 2
        st.session_state.ai_chips += pot // 2

    st.session_state.pot = 0
    st.markdown("---")

    if st.button("Siguiente Ronda ➡️"):
        st.session_state.game_state = 'start'
        st.rerun()

# --- Controles Adicionales ---
st.markdown("---")
if st.button("Reiniciar Partida Completa 🔄"):
    st.session_state.game_state = 'start'
    st.session_state.player_chips = 1000
    st.session_state.ai_chips = 1000
    st.session_state.pot = 0
    st.rerun()