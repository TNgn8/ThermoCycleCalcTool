import math
import numpy as np
import tkinter as tk
import matplotlib.pyplot as plt
from tkinter import ttk
from tkinter import messagebox
from tkinter import font as tkfont
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
from matplotlib.colors import to_rgb, to_hex


# Definition der globalen Summe der Wärmemengen
global_summe_q = 0

# Globale Liste zur Speicherung der Zustände
state_history = []


class StateFrame:
    def __init__(self, master, label_text, row, column, first_state=False):
        self.first_state = first_state
        self.frame = tk.Frame(master, bd=2, relief="groove")
        self.frame.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")

        self.label = tk.Label(self.frame, text=label_text, font=("Arial", 13, "bold"))
        self.label.grid(row=0, column=0, columnspan=2)

        self.labels = ["Temperature [K]:", "Pressure [bar]:", "Volume [m3/kg]:"]
        self.additional_labels = ["Enthalpy [kJ/kg]:", "Entropy [J/kg]:"]
        self.entries = []

        for i, text in enumerate(self.labels, 1):
            label = tk.Label(self.frame, text=text)
            label.grid(row=i, column=0, sticky="e")
            entry = tk.Entry(self.frame)
            entry.grid(row=i, column=1, sticky="ew")
            self.entries.append((label, entry))
            if not first_state:
                entry.configure(state='disabled')


        self.additional_entries = []
        for i, text in enumerate(self.additional_labels,
                                 len(self.labels)+1):  # Zusätzliche Felder erstellen, aber zunächst verbergen
            label = tk.Label(self.frame, text=text)
            entry = tk.Entry(self.frame)
            self.additional_entries.append((label, entry))  # Speichern, um später anzuzeigen

        self.additional_fields_visible = False  # Status für zusätzliche Felder

        self.toggle_button = tk.Button(self.frame, text="Show more", command=self.toggle_fields)
        self.toggle_button.grid(row=6, column=0, columnspan=2)

        self.frame.columnconfigure(1, weight=1)

    def toggle_fields(self):
        if self.additional_fields_visible:
            for label, entry in self.additional_entries:  # Zusätzliche Felder ausblenden
                label.grid_remove()
                entry.grid_remove()
            self.toggle_button.config(text="Show more")
        else:
            for i, (label, entry) in enumerate(self.additional_entries, start=len(self.labels)+1):
                label.grid(row=i, column=0, sticky="e")
                entry.grid(row=i, column=1, sticky="ew")
            self.toggle_button.config(text="Show less")
        self.additional_fields_visible = not self.additional_fields_visible

    def clear_fields(self):
        entry_fields = [entry for _, entry in self.entries]

        # Alle Felder aktivieren, leeren und dann deaktivieren
        for entry in entry_fields:
            entry.configure(state='normal')
            entry.delete(0, tk.END)
            if not self.first_state or entry_fields.index(entry) >= 3:
                entry.configure(state='readonly')

        additional_entry_fields = [entry for _, entry in self.additional_entries]
        for entry in additional_entry_fields:
            entry.configure(state='normal')
            entry.delete(0, tk.END)
            entry.configure(state='readonly')


class ProcessFrame:
    def __init__(self, master, label_text, row, column):
        self.frame = tk.Frame(master, bd=2)
        self.frame.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")

        self.label = tk.Label(self.frame, text=label_text, font=("Arial", 13, "bold"))  # Überschrift für das Frame
        self.label.grid(row=0, column=1, sticky="ew")

        # Container für die Inhalte erstellen, die ein- und ausgeblendet werden sollen
        self.content_frame = tk.Frame(self.frame)
        self.content_frame.grid(row=1, column=1, sticky="nsew")

        self.properties = ["Heat Transfer [kJ/kg]", "Thermodynamic Work [kJ/kg]", "Internal Energy [kJ/kg]"]
        self.entries = []

        for i, prop in enumerate(self.properties, start=1):
            label = tk.Label(self.content_frame, text=f"{prop}:")
            label.grid(row=i, column=1, sticky="w")
            entry = tk.Entry(self.content_frame)
            entry.grid(row=i, column=2, sticky="ew")
            entry.configure(state='readonly')
            self.entries.append(entry)

        # Konfiguration der Spalten für die Zentrierung
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=2)
        self.frame.columnconfigure(2, weight=1)
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.columnconfigure(1, weight=2)
        self.content_frame.columnconfigure(2, weight=2)
        self.content_frame.columnconfigure(3, weight=1)

        # Inhalt anfangs ausblenden
        self.content_frame.grid_remove()

    # Funktion, um den Inhalt ein- oder auszublenden
    def toggle_content(self):
        if self.content_frame.winfo_viewable():
            self.content_frame.grid_remove()
        else:
            self.content_frame.grid()

    def update_title(self, new_title):
        self.label.config(text=new_title)

    def clear_fields(self):
        for entry in self.entries:
            entry.configure(state='normal')
            entry.delete(0, tk.END)
            entry.configure(state='readonly')


def are_fields_filled():
    # Prüfen, ob die benötigten Felder ausgefüllt sind und numerisch sind
    required_fields = [compression_ratio_entry, heat_or_injection_entry]  # Liste der erforderlichen Felder
    for field in required_fields:
        field_value = field.get().strip()
        if field_value == "":  # Prüft, ob das Feld leer ist
            messagebox.showerror("Missing Input", "Please fill in all fields.")
            return False
        try:
            field_float = float(field_value)
            if field_float == 0:
                messagebox.showerror("Invalid Input", "Values cannot be zero.")
                return False
        except ValueError:
            messagebox.showerror("Invalid Input", "Values must be numerical or use . instead of , !")
            return False

    # Überprüfe, ob die ersten drei Felder im ersten Zustand ausgefüllt sind und numerisch sind
    if state1_frame.first_state:
        for label, entry in state1_frame.entries[:3]:
            field_value = entry.get().strip()
            if field_value == "":
                messagebox.showerror("Missing Input", "Please fill in all fields in the first state.")
                return False
            try:
                field_float = float(field_value)
                if field_float == 0:
                    messagebox.showerror("Invalid Input", "Values cannot be zero.")
                    return False
            except ValueError:
                messagebox.showerror("Invalid Input", "Values must be numerical or use . instead of , !")
                return False

    return True


def get_values_from_StateFrame(state_frame):
    # Überprüfe zuerst, ob alle benötigten Felder ausgefüllt sind
    if not are_fields_filled():
        return None

    v = float(state_frame.entries[2][1].get())
    p = float(state_frame.entries[1][1].get())
    t = float(state_frame.entries[0][1].get())
    cp = float(entries[0].get())  # Cp aus Entry holen
    cv = float(entries[1].get())  # Cv aus Entry holen
    k = float(entries[2].get())
    z = float(compression_ratio_entry.get())
    q = float(heat_or_injection_entry.get())

    return v, p, t, cp, cv, k, z, q


def format_value(value):
    formatted_value = f"{value:.2f}"
    # Prüft, ob die Zahl mit ".00" endet, was bedeutet, keine Nachkommastellen sind nötig.
    if formatted_value.endswith("00"):
        return f"{value:.0f}"
    # Prüft, ob die vorletzte Ziffer eine 0 ist und fügt eine zusätzliche Nachkommastelle hinzu, wenn ja.
    elif formatted_value[-2] == "0":
        return f"{value:.3f}"
    return formatted_value


def update_state_and_process(state_frame, process_frame, t, p, v, h, s, q, w, u):
    # Werte formatieren vor dem Einfügen in die GUI
    t_str = format_value(t)
    p_str = format_value(p)
    v_str = format_value(v)
    h_str = format_value(h)
    s_str = format_value(s)
    q_str = format_value(q)
    w_str = format_value(w)
    u_str = format_value(u)

    # Liste der zu aktualisierenden Felder in StateFrame und ProcessFrame
    state_fields = [
        state_frame.entries[0][1],
        state_frame.entries[1][1],
        state_frame.entries[2][1],
        state_frame.additional_entries[0][1],
        state_frame.additional_entries[1][1]
    ]

    process_fields = [
        process_frame.entries[0],
        process_frame.entries[1],
        process_frame.entries[2]
    ]

    # Alle Felder aktivieren, Werte einfügen
    for i, (field, value) in enumerate(zip(state_fields, [t_str, p_str, v_str, h_str, s_str])):
        field.configure(state='normal')
        field.delete(0, tk.END)
        field.insert(0, value)
        # Setze nur die zusätzlichen Felder oder Felder von anderen States auf readonly
        if i > 2 or not state_frame.first_state:
            field.configure(state='readonly')

    for field, value in zip(process_fields, [q_str, w_str, u_str]):
        field.configure(state='normal')
        field.delete(0, tk.END)
        field.insert(0, value)
        field.configure(state='readonly')


def isentropic_change(vorheriger_state_frame, nachfolgender_state_frame, process_frame, letzter_durchlauf=False):
    global global_summe_q
    global state_history
    v1, p1, t1, cp, cv, k, z, q = get_values_from_StateFrame(vorheriger_state_frame)

    # Save data in state history
    actual_state = {'t': t1, 'p': p1, 'v': v1}
    state_history.append(actual_state)

    # Den Titel des aktuellen ProcessFrame überprüfen
    titel = process_frame.label.cget("text").lower()
    if "compression" in titel:
        if process_combobox.get() == "Joule":
            # z is in this case the pressureratio z = p2/p1
            t2 = t1 * z ** ((k - 1) / k)
            p2 = z * p1
            v2 = v1 * (p1 / p2) ** (1 / k)
        else:
            t2 = t1 * (z ** (k - 1))
            v2 = v1 / z  # Für eine isentropische Zustandsänderung in einem idealen Gas
            p2 = p1 * (z ** k)
    elif "expansion" in titel:
        if process_combobox.get() == "Diesel":
            second_state = state_history[1]
            v = second_state['v']
            v2 = v * z
            p2 = p1 * ((v1 / v2) ** k)
            t2 = t1 * ((v1 / v2) ** (k - 1))
        elif process_combobox.get() == "Joule":
            # z is in this case the pressureratio z = p3/p4
            t2 = t1 * (1 / z) ** ((k - 1) / k)
            p2 = p1 / z
            v2 = v1 * (p1 / p2) ** (1 / k)
        else:
            t2 = t1 * ((1 / z) ** (k - 1))
            v2 = v1 * z
            p2 = p1 * ((1/z) ** k)
    else:
        t2, p2, v2 = None, None, None  # Wenn keines von den beiden zustimmt

    h2 = cp * (t2 - t1) / 1000
    s2 = 0
    q = 0

    if letzter_durchlauf:
        w = -global_summe_q  # u auf den negativen Wert der globalen Summe setzen
        u = w
    else:
        u = cv * (t2 - t1) / 1000
        w = u
        global_summe_q += w  # Addiere die Arbeit zur globalen Summe

    update_state_and_process(nachfolgender_state_frame, process_frame, t2, p2, v2, h2, s2, q, w, u)


def isochoric_change(vorheriger_state_frame, nachfolgender_state_frame, process_frame, letzter_durchlauf=False):
    global global_summe_q
    global state_history
    v1, p1, t1, cp, cv, k, z, q = get_values_from_StateFrame(vorheriger_state_frame)


    actual_state = {'t': t1, 'p': p1, 'v': v1}
    state_history.append(actual_state)

    # Wärmemenge für den letzten Durchlauf anpassen
    if letzter_durchlauf:
        q = global_summe_q

    # Den Titel des aktuellen ProcessFrame überprüfen
    titel = process_frame.label.cget("text").lower()
    if "output" in titel:
        q = q * -1
    else:
        q = q

    if not letzter_durchlauf:
        # Update der globalen Summe der Wärmemengen, außer im letzten Durchlauf
        global_summe_q += q

    v2 = v1
    t2 = t1 + q / cv * 1000
    p2 = p1 * (t2 / t1)
    h2 = cp * (t2 - t1) / 1000
    u = cv * (t2 - t1) / 1000
    w = 0
    try:
        # Versuche, s2 zu berechnen. Dies könnte Fehler werfen, wenn t1 oder t2 nicht gültige Werte für math.log sind.
        s2 = cv * math.log(t2 / t1)
    except Exception as e:
        # Fängt jegliche Art von Ausnahme ab, die beim Versuch, s2 zu berechnen, auftritt.
        messagebox.showerror("Error", "Error calculating entropy: " + str(e))
        s2 = None  # Optional: Setze s2 auf einen Fehlerwert oder handle den Fehler anderweitig.

    update_state_and_process(nachfolgender_state_frame, process_frame, t2, p2, v2, h2, s2, q, w, u)


def isothermal_change(vorheriger_state_frame, nachfolgender_state_frame, process_frame, letzter_durchlauf=False):
    global global_summe_q
    global state_history
    v1, p1, t1, cp, cv, k, z, q = get_values_from_StateFrame(vorheriger_state_frame)
    R = cp - cv

    actual_state = {'t': t1, 'p': p1, 'v': v1}
    state_history.append(actual_state)

    # Den Titel des aktuellen ProcessFrame überprüfen
    titel = process_frame.label.cget("text").lower()
    if "compression" in titel:
        v2 = v1 / z
    elif "expansion" in titel:
        v2 = v1 * z
    else:
        t2, p2, v2 = None, None, None

    t2 = t1
    p2 = p1 * v1 / v2
    h2 = cp * (t2 - t1) / 1000
    s2 = cv * math.log(p2 / p1) + cp * math.log(v2 / v1)

    u = 0

    if letzter_durchlauf:
        w = -global_summe_q
        q = -w
    else:
        w = -R * t2 * math.log(p1 / p2) / 1000
        q = -w
        global_summe_q += w + q  # Addiere die Arbeit zur globalen Summe

    update_state_and_process(nachfolgender_state_frame, process_frame, t2, p2, v2, h2, s2, q, w, u)


def isobaric_change(vorheriger_state_frame, nachfolgender_state_frame, process_frame, letzter_durchlauf=False):
    global global_summe_q
    global state_history
    v1, p1, t1, cp, cv, k, z, q = get_values_from_StateFrame(vorheriger_state_frame)
    R = cp - cv

    actual_state = {'t': t1, 'p': p1, 'v': v1}
    state_history.append(actual_state)

    # Den Titel des aktuellen ProcessFrame überprüfen
    titel = process_frame.label.cget("text").lower()
    if "output" in titel:
        # Wärmemenge für den letzten Durchlauf anpassen
        vorzeichen = -1
        if letzter_durchlauf:
            first_state = state_history[0]
            t2 = first_state['t']
            v2 = v1 * t2 / t1
            w = -(v2 - v1) * R * t2 / v2 / 1000
            global_summe_q += w  # w des aktuellen Zustandes wird in die Energiebilanz mit einberechnet
            q = global_summe_q * vorzeichen
        else:
            t2 = t1 + q * vorzeichen * 1000 / cp
    else:
        t2 = t1 + q * 1000 / cp
        if process_combobox.get() == "Diesel":
            phi = q  # q ist hier das Injektionsverhältnis
            t2 = t1 * abs(phi)  # Injektionsverhältnis immer positiv

    p2 = p1
    v2 = v1 * t2 / t1
    h2 = cp * (t2 - t1) / 1000
    s2 = cp * math.log(t2 / t1)
    w = -(v2 - v1) * R * t2 / v2 / 1000
    u = cv * (t2 - t1) / 1000

    if not letzter_durchlauf:
        q = cp * (t2 - t1) / 1000
        # Update der globalen Summe der Wärmemengen, außer im letzten Durchlauf
        global_summe_q += q + w

    update_state_and_process(nachfolgender_state_frame, process_frame, t2, p2, v2, h2, s2, q, w, u)


def determine_and_calculate_process_change(vorheriger_state_frame, nachfolgender_state_frame, process_frame,
                                            letzter_durchlauf=False):
    titel = process_frame.label.cget("text").lower()
    if "isentrop" in titel:
        isentropic_change(vorheriger_state_frame, nachfolgender_state_frame, process_frame)
    elif "isochor" in titel:
        isochoric_change(vorheriger_state_frame, nachfolgender_state_frame, process_frame,
                         letzter_durchlauf=letzter_durchlauf)
    elif "isotherm" in titel:
        isothermal_change(vorheriger_state_frame, nachfolgender_state_frame, process_frame)
    elif "isobar" in titel:
        isobaric_change(vorheriger_state_frame, nachfolgender_state_frame, process_frame,
                        letzter_durchlauf=letzter_durchlauf)


def update_efficiency_display(efficiency):
    efficiency_entry.config(state='normal')  # Feld zum Editieren freigeben
    efficiency_entry.delete(0, tk.END)  # Vorherigen Inhalt löschen
    efficiency_entry.insert(0, f"{efficiency:.2f}")  # Berechneten Wirkungsgrad einfügen
    efficiency_entry.config(state='readonly')  # Feld wieder sperren


def calculate_efficiency():
    process = process_combobox.get()
    efficiency = 0
    t_min = float(state1_frame.entries[0][1].get())
    t_max = float(state3_frame.entries[0][1].get())
    p_min = float(state1_frame.entries[1][1].get())
    p_max = float(state3_frame.entries[1][1].get())
    z = float(compression_ratio_entry.get())
    phi = float(heat_or_injection_entry.get())
    k = float(entries[2].get())
    if process == "Otto":
        efficiency = (1 - 1 / (z ** (k - 1))) * 100
    elif process == "Diesel":
        efficiency = (1 - (1 / (k * z ** (k - 1)) * (phi ** k - 1 ) / (phi - 1))) * 100
    elif process == "Stirling":
        efficiency = (1 - t_min / t_max) * 100
    elif process == "Joule":
        efficiency = (1 - (p_min / p_max) ** ((k - 1) / k)) * 100

    update_efficiency_display(efficiency)


def perform_calculations():
    global global_summe_q
    global_summe_q = 0  # Zurücksetzen der Summe der Wärmemengen zu Beginn der Berechnung
    state_history.clear()

    for i in range(len(process_frames)):
        vorheriger_state_frame = [state1_frame, state2_frame, state3_frame, state4_frame][i]
        nachfolgender_state_frame = [state2_frame, state3_frame, state4_frame, state1_frame][i]
        process_frame = process_frames[i]
        if i < len(process_frames) - 1:  # Für alle außer dem letzten Durchlauf
            determine_and_calculate_process_change(vorheriger_state_frame, nachfolgender_state_frame,
                                                    process_frame)
        else:  # Im letzten Durchlauf
            determine_and_calculate_process_change(vorheriger_state_frame, nachfolgender_state_frame,
                                                    process_frame, letzter_durchlauf=True)

    # Berechnung des Wirkungsgrads hinzufügen
    calculate_efficiency()


def create_pv_diagram(ax):
    k = float(entries[2].get())
    step_number = 1

    for i, process_frame in enumerate(process_frames):
        start_state_frame = [state1_frame, state2_frame, state3_frame, state4_frame][i]
        end_state_frame = [state2_frame, state3_frame, state4_frame, state1_frame][i]
        p1, v1 = float(start_state_frame.entries[1][1].get()), float(start_state_frame.entries[2][1].get())
        p2, v2 = float(end_state_frame.entries[1][1].get()), float(end_state_frame.entries[2][1].get())

        # Zeichnet die Verbindungslinien ohne Marker
        if "isentropic" in process_frame.label.cget("text").lower():
            volumes = np.linspace(min(v1, v2), max(v1, v2), 100)
            pressures = p1 * (v1 ** k) / (volumes ** k) if v1 < v2 else p2 * (v2 ** k) / (volumes ** k)
            ax.plot(volumes, pressures, linestyle='-', label=process_frame.label.cget("text"))
        elif "isothermal" in process_frame.label.cget("text").lower():
            volumes = np.linspace(min(v1, v2), max(v1, v2), 100)
            pressures = p1 * v1 / volumes
            ax.plot(volumes, pressures, linestyle='-', label=process_frame.label.cget("text"))
        else:
            ax.plot([v1, v2], [p1, p2], linestyle='-', label=process_frame.label.cget("text"))

        # Markiert die Eckpunkte der Zustände
        ax.plot([v1, v2], [p1, p2], 'o', label='')  # Leeres Label, um Duplikate in der Legende zu vermeiden
        ax.annotate(str(step_number), (v1, p1), textcoords="offset points", xytext=(10, 0), ha='right')
        step_number += 1

    ax.set_title('p-V Diagram')
    ax.set_xlabel('Volume [m3/kg]')
    ax.set_ylabel('Pressure [bar]')
    ax.legend()


def create_ts_diagram(ax):
    cp = float(entries[0].get())
    cv = float(entries[1].get())
    R = cp - cv

    list_delta_S = [0]
    step_number = 1

    for i, process_frame in enumerate(process_frames):
        start_state_frame = [state1_frame, state2_frame, state3_frame, state4_frame][i]
        end_state_frame = [state2_frame, state3_frame, state4_frame, state1_frame][i]
        p1, v1, T1, s1 = (float(start_state_frame.entries[1][1].get()),
                        float(start_state_frame.entries[2][1].get()),
                        float(start_state_frame.entries[0][1].get()),
                        float(start_state_frame.additional_entries[1][1].get()))
        p2, v2, T2, s2 = (float(end_state_frame.entries[1][1].get()),
                        float(end_state_frame.entries[2][1].get()),
                        float(end_state_frame.entries[0][1].get()),
                        float(end_state_frame.additional_entries[1][1].get()))

        if "isentrop" in process_frame.label.cget("text").lower():
            # Überprüfe, ob es der erste Durchgang ist
            if i == 0:   # Wenn ja, setze den Startwert der Entropie auf 0
                s1 = 0
            else:
                s1 = float(start_state_frame.additional_entries[1][1].get())
                s2 = s1
            ax.plot([s1, s2], [T1, T2], linestyle='-', label=process_frame.label.cget("text"))
            list_delta_S.append(s2)
            ax.plot(s2, T2, 'o', label='')  # Zeichne den Endpunkt
            ax.annotate(str(step_number), (s1, T1), textcoords="offset points", xytext=(10, 0), ha='right')
        elif "isochor" in process_frame.label.cget("text").lower():
            if process_combobox.get() == "Stirling":
                start_delta_S = list_delta_S[-1]
                temperatures = np.linspace(T1, T2, 100)  # Erzeuge 100 Zwischentemperaturen
                delta_S = start_delta_S + cv * np.log(temperatures / T1) if T1 < T2 else\
                    cv * np.log(temperatures / T2)   # Berechnung der Entropieänderung für jede Zwischentemperatur
                s2 = delta_S[-1]
                list_delta_S.append(s2)  # Nur den letzten Wert aus dem Array speichern
                ax.plot(delta_S, temperatures, linestyle='-', label=process_frame.label.cget("text"))
            else:
                temperatures = np.linspace(T1, T2, 100)  # Erzeuge 100 Zwischentemperaturen
                delta_S = cv * np.log(temperatures / T1) if T1 < T2 else\
                    cv * np.log(temperatures / T2)   # Berechnung der Entropieänderung für jede Zwischentemperatur
                ax.plot(delta_S, temperatures, linestyle='-', label=process_frame.label.cget("text"))
                s2 = delta_S[-1]
                list_delta_S.append(s2)
            if i == 3:
                s2 = 0
                s1 = list_delta_S[-2]
                ax.plot(s2, T2, 'o', label='')  # Zeichne den Endpunkt
            else:
                ax.plot(s2, T2, 'o', label='')  # Zeichne den Endpunkt
            ax.annotate(str(step_number), (s1, T1), textcoords="offset points", xytext=(10, 0), ha='right')
        elif "isobar" in process_frame.label.cget("text").lower():
            temperatures = np.linspace(T1, T2, 100)  # Erzeuge 100 Zwischentemperaturen
            delta_S = cp * np.log(temperatures / T1) if T1 < T2 else cp * np.log(temperatures / T2)
            ax.plot(delta_S, temperatures, linestyle='-', label=process_frame.label.cget("text"))
            if i == 3:
                ax.plot(0, T2, 'o', label='')  # Zeichne den Endpunkt
                s1 = list_delta_S[-1]
            else:
                ax.plot(s2, T2, 'o', label='')  # Zeichne den Endpunkt
            ax.annotate(str(step_number), (s1, T1), textcoords="offset points", xytext=(10, 0), ha='right')
        elif "isotherm" in process_frame.label.cget("text").lower():
            if i == 0:  # Setze den ersten Punkt der Entropie auf 0 nur für den ersten Durchgang
                temperatures = T1  # Temperatur bleibt konstant
                pressures = np.linspace(p1, p2, 100)  # Erzeuge 100 Zwischenwerte für den Druck
                volumes = p1 * v1 / pressures  # Berechnung der Zwischenvolumen basierend auf dem idealen Gasgesetz
                delta_S = R * np.log(volumes / v1)  # Berechnung der Entropieänderung
                s2 = delta_S[-1]
                s1 = list_delta_S[-1]   # Anfangsentropie auf 0 setzen
                list_delta_S.append(s2)
                delta_S -= delta_S[0]
            else:
                start_delta_S = list_delta_S[-1]
                temperatures = T1  # Temperatur bleibt konstant
                pressures = np.linspace(p1, p2, 100)  # Erzeuge 100 Zwischenwerte für den Druck
                volumes = p1 * v1 / pressures  # Berechnung der Zwischenvolumen basierend auf dem idealen Gasgesetz
                delta_S = start_delta_S + R * np.log(volumes / v1)  # Berechnung der Entropieänderung
                s2 = delta_S[-1]
                s1 = abs(list_delta_S[-1])
                list_delta_S.append(s2)

            ax.plot(delta_S, [temperatures] * 100, linestyle='-', label=process_frame.label.cget("text"))
            ax.plot(s2, T2, 'o', label='')  # Zeichne den Endpunkt
            ax.annotate(str(step_number), (s1, T1), textcoords="offset points", xytext=(10, 0), ha='right')

        step_number += 1

    ax.set_title('T-s Diagram')
    ax.set_xlabel('Entropy [J/kg]')
    ax.set_ylabel('Temperature [K]')
    ax.legend()
    ax.text(0.5, 0.95, "Assumed state: 0°C, 1 atm", transform=ax.transAxes,
            horizontalalignment='center', verticalalignment='center',
            fontsize=10, color='gray', alpha=0.8)


def show_diagrams():
    diagram_window = tk.Toplevel(root)
    diagram_window.title("Thermodynamic Diagrams")
    diagram_window.geometry('600x800')

    diagram_width = 600
    diagram_height = 800
    screen_width = diagram_window.winfo_screenwidth()
    screen_height = diagram_window.winfo_screenheight()
    x_offset = (screen_width - diagram_width) // 2
    y_offset = (screen_height - diagram_height) // 2

    # Fensterposition und Größe festlegen
    diagram_window.geometry(f'{diagram_width}x{diagram_height}+{x_offset+300}+{y_offset}')

    # Die Größe und Auflösung der Figur werden angepasst
    fig = Figure(figsize=(6, 10), dpi=100)

    # P-v Diagramm in der oberen Hälfte
    ax_pv = fig.add_subplot(2, 1, 1)
    create_pv_diagram(ax_pv)

    # T-s Diagramm in der unteren Hälfte
    ax_ts = fig.add_subplot(2, 1, 2)
    create_ts_diagram(ax_ts)

    # Anwendung von tight_layout zur Vermeidung von Überlappungen
    fig.tight_layout()

    # Das Diagramm im neuen Fenster anzeigen
    canvas = FigureCanvasTkAgg(fig, master=diagram_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


def clamp_color(value):
    return max(0, min(1, value))


def otto_animation():
    # Parameter
    kolben_breite = 0.7
    kolben_hoehe = 0.2
    kolben_min = 0.3
    kolben_max = 1.5
    zylinder_breite = 0.7
    zylinder_hoehe = 2.0

    # Bewegungserzeugung
    auf_bewegung_frames = np.linspace(0, np.pi, 50)  # Isentropische Kompression
    pause_oben_frames = np.ones(40) * np.pi  # Isochore Wärmezufuhr
    ab_bewegung_frames = np.linspace(np.pi, 2 * np.pi, 40)  # Isentropische Expansion
    pause_unten_frames = np.ones(40) * 0  # Isochore Wärmeabfuhr

    # Ändere die Reihenfolge, damit die Kompression zuerst startet
    gesamte_frames = np.concatenate([auf_bewegung_frames, pause_oben_frames, ab_bewegung_frames, pause_unten_frames,
                                     pause_unten_frames])

    fig, ax = plt.subplots()
    ax.set_xlim(0, 2)
    ax.set_ylim(0, 3)
    ax.axis('off')

    zylinder = plt.Rectangle((1 - zylinder_breite / 2, 0), zylinder_breite, zylinder_hoehe, fill=None,
                             edgecolor='black')
    ax.add_patch(zylinder)

    kolben = plt.Rectangle((1 - kolben_breite / 2, kolben_min), kolben_breite, kolben_hoehe, fc='black')
    ax.add_patch(kolben)

    raum = plt.Rectangle((1 - zylinder_breite / 2, kolben_max), zylinder_breite, zylinder_hoehe - kolben_max,
                         color='blue')
    ax.add_patch(raum)

    # Text für die Phase hinzufügen
    phase_text = ax.text(1, 2.5, '', ha='center', va='center', fontsize=12, color='black')

    start_color = to_rgb('blue')
    combustion_color = to_rgb('red')
    orange = to_rgb('orange')

    def init():
        global stiel
        stiel_start = (1, kolben_min + kolben_hoehe / 2)
        stiel_ende = (1, 0)
        stiel = plt.Line2D((stiel_start[0], stiel_ende[0]), (stiel_start[1], stiel_ende[1]), lw=2,
                           color='black')
        ax.add_line(stiel)
        return kolben, raum, stiel, phase_text

    def update(frame):
        y_pos = kolben_min + (kolben_max - kolben_min) * (0.5 * (1 - np.cos(gesamte_frames[frame])))
        kolben.set_y(y_pos)

        # Phasen-Management und Farbübergänge
        if frame < len(auf_bewegung_frames):
            phase_text.set_text('Isentropic Compression 1 → 2')
            progress = frame / len(auf_bewegung_frames)
            current_color = [clamp_color(start_color[i] + progress * (orange[i] - start_color[i])) for i in range(3)]
        elif frame < len(auf_bewegung_frames) + len(pause_oben_frames):
            phase_text.set_text('Isochoric Heat Input 2 → 3')
            index = frame - len(auf_bewegung_frames)
            progress = index / len(pause_oben_frames)
            current_color = [clamp_color(orange[i] + progress * (combustion_color[i] - orange[i])) for i in range(3)]
        elif frame < len(auf_bewegung_frames) + len(pause_oben_frames) + len(ab_bewegung_frames):
            phase_text.set_text('Isentropic Expansion 3 → 4')
            index = frame - len(auf_bewegung_frames) - len(pause_oben_frames)
            progress = index / len(ab_bewegung_frames)
            current_color = [clamp_color(combustion_color[i] + progress * (orange[i] - combustion_color[i]))
                             for i in range(3)]
        else:
            phase_text.set_text('Isochoric Heat Output 4 → 1')
            index = frame - len(auf_bewegung_frames) - len(pause_oben_frames) - len(ab_bewegung_frames)
            progress = index / len(pause_unten_frames)
            current_color = [clamp_color(orange[i] + progress * (start_color[i] - orange[i])) for i in range(3)]

        raum.set_color(to_hex(current_color))

        raum.set_height(zylinder_hoehe - y_pos - kolben_hoehe)
        raum.set_y(y_pos + kolben_hoehe)

        stiel_start_y = y_pos + kolben_hoehe / 2
        stiel.set_ydata([stiel_start_y, 0])
        return kolben, raum, stiel, phase_text

    ani = FuncAnimation(fig, update, frames=len(gesamte_frames), init_func=init, blit=True, interval=20)
    plt.show()


def diesel_animation():
    # Parameter
    kolben_breite = 0.7
    kolben_hoehe = 0.2
    kolben_min = 0.3
    kolben_max = 1.5
    zylinder_breite = 0.7
    zylinder_hoehe = 2.0

    # Bewegungserzeugung
    auf_bewegung_frames = np.linspace(0, np.pi, 50)
    isobar_frames = np.linspace(np.pi, 1.5 * np.pi, 50)
    ab_bewegung_frames = np.linspace(1.5 * np.pi, 2 * np.pi, 60)
    pause_unten_frames = np.ones(50) * 0

    gesamte_frames = np.concatenate([auf_bewegung_frames, isobar_frames, ab_bewegung_frames, pause_unten_frames])

    fig, ax = plt.subplots()
    ax.set_xlim(0, 2)
    ax.set_ylim(0, 3)
    ax.axis('off')

    zylinder = plt.Rectangle((1 - zylinder_breite / 2, 0), zylinder_breite, zylinder_hoehe, fill=None,
                             edgecolor='black')
    ax.add_patch(zylinder)

    kolben = plt.Rectangle((1 - kolben_breite / 2, kolben_min), kolben_breite, kolben_hoehe, fc='black')
    ax.add_patch(kolben)

    raum = plt.Rectangle((1 - zylinder_breite / 2, kolben_max), zylinder_breite, zylinder_hoehe - kolben_max,
                         color='blue')
    ax.add_patch(raum)

    # Text für die Phase hinzufügen
    phase_text = ax.text(1, 2.5, '', ha='center', va='center', fontsize=12, color='black')

    start_color = to_rgb('blue')
    combustion_color = to_rgb('red')
    orange = to_rgb('orange')

    def init():
        global stiel
        stiel_start = (1, kolben_min + kolben_hoehe / 2)
        stiel_ende = (1, 0)
        stiel = plt.Line2D((stiel_start[0], stiel_ende[0]), (stiel_start[1], stiel_ende[1]), lw=2,
                           color='black')
        ax.add_line(stiel)
        return kolben, raum, stiel, phase_text

    def update(frame):
        y_pos = kolben_min + (kolben_max - kolben_min) * (0.5 * (1 - np.cos(gesamte_frames[frame])))
        kolben.set_y(y_pos)
        raum.set_height(zylinder_hoehe - y_pos - kolben_hoehe)
        raum.set_y(y_pos + kolben_hoehe)

        # Berechnen des aktuellen Frames innerhalb jeder Phase
        if frame < len(auf_bewegung_frames):
            phase_text.set_text('Isentropic Compression 1 → 2')
            progress = frame / len(auf_bewegung_frames)
            current_color = tuple([clamp_color(start_color[i] + progress * (combustion_color[i] - start_color[i]))
                                   for i in range(3)])
        elif frame < len(auf_bewegung_frames) + len(isobar_frames):
            phase_text.set_text('Isobaric Heat Input 2 → 3')
            index = frame - len(auf_bewegung_frames)
            progress = index / len(isobar_frames)
            current_color = tuple([clamp_color(combustion_color[i] + progress * (orange[i] - combustion_color[i]))
                                   for i in range(3)])
        elif frame < len(auf_bewegung_frames) + len(isobar_frames) + len(ab_bewegung_frames):
            phase_text.set_text('Isentropic Expansion 3 → 4')
            index = frame - len(auf_bewegung_frames) - len(isobar_frames)
            progress = index / len(ab_bewegung_frames)
            current_color = orange
        else:
            phase_text.set_text('Isochoric Heat Output 4 → 1')
            progress = ((frame - len(auf_bewegung_frames) - len(isobar_frames) - len(ab_bewegung_frames)) /
                        len(pause_unten_frames))
            current_color = tuple([clamp_color(orange[i] + progress * (start_color[i] - orange[i])) for i in range(3)])

        raum.set_color(to_hex(current_color))

        stiel_start_y = y_pos + kolben_hoehe / 2
        stiel.set_ydata([stiel_start_y, 0])
        return kolben, raum, stiel, phase_text

    ani = FuncAnimation(fig, update, frames=len(gesamte_frames), init_func=init, blit=True, interval=20)
    plt.show()


def stirling_animation():
    # Parameter
    kolben_breite = 0.7
    kolben_hoehe = 0.2
    kolben_min = 0.3
    kolben_max = 0.7
    verdr_kolben_hoehe = 0.5
    verdr_kolben_start = 1.4  # Startposition des Verdrängerkolbens
    verdr_kolben_end = 1.0    # Endposition des Verdrängerkolbens während der isochoren Phase
    zylinder_breite = 0.7
    zylinder_hoehe = 2.0

    # Bewegungserzeugung
    kompression_frames = np.linspace(0, np.pi, 50)
    heat_input_frames = np.linspace(0, np.pi, 50)
    expansion_frames = np.linspace(np.pi, 2 * np.pi, 50)
    heat_output_frames = np.linspace(0, np.pi, 80)

    # Gesamte Bewegung kombinieren
    gesamte_frames = np.concatenate([kompression_frames, heat_input_frames, expansion_frames, heat_output_frames])

    # Figure und Axes
    fig, ax = plt.subplots()
    ax.set_xlim(0, 2)
    ax.set_ylim(0, 3)
    ax.axis('off')

    # Zylinderzeichnung
    zylinder = plt.Rectangle((1 - zylinder_breite / 2, 0), zylinder_breite, zylinder_hoehe, fill=None,
                             edgecolor='black')
    ax.add_patch(zylinder)

    # Arbeitskolbenzeichnung
    kolben = plt.Rectangle((1 - kolben_breite / 2, kolben_min), kolben_breite, kolben_hoehe, fc='black')
    ax.add_patch(kolben)

    # Verdrängerkolbenzeichnung
    verdr_kolben = plt.Rectangle((1 - kolben_breite / 2, verdr_kolben_start), kolben_breite, verdr_kolben_hoehe,
                                 fc='red')
    ax.add_patch(verdr_kolben)

    # Text für die Phase hinzufügen
    phase_text = ax.text(1, 2.5, '', ha='center', va='center', fontsize=12, color='black')

    def init():
        global stiel
        stiel_start = (1, kolben_min + kolben_hoehe / 2)
        stiel_ende = (1, 0)
        stiel = plt.Line2D((stiel_start[0], stiel_ende[0]), (stiel_start[1], stiel_ende[1]), lw=2,
                           color='black')
        ax.add_line(stiel)
        return kolben, verdr_kolben, stiel, phase_text

    def update(frame):
        phase_len = len(kompression_frames)
        if frame < phase_len:  # Isothermal Compression
            y_pos = kolben_min + (kolben_max - kolben_min) * (0.5 * (1 - np.cos(gesamte_frames[frame])))
            kolben.set_y(y_pos)
            phase_text.set_text('Isothermal Compression 1 → 2')
        elif phase_len <= frame < 2 * phase_len:  # Isochoric Heat Addition
            verdr_y_pos = (verdr_kolben_start - (verdr_kolben_start - verdr_kolben_end) *
                           (0.5 * (1 - np.cos(gesamte_frames[frame]))))
            verdr_kolben.set_y(verdr_y_pos)
            phase_text.set_text('Isochoric Heat Input 2 → 3')
        elif 2 * phase_len <= frame < 3 * phase_len:  # Isothermal Expansion
            y_pos = kolben_max - (kolben_max - kolben_min) * (0.5 * (1 + np.cos(gesamte_frames[frame])))
            kolben.set_y(y_pos)
            verdr_y_pos = y_pos + kolben_hoehe + 0.1
            verdr_kolben.set_y(verdr_y_pos)
            phase_text.set_text('Isothermal Expansion 3 → 4')
        elif 3 * phase_len <= frame < 4 * phase_len:  # Isochoric Heat Removal
            verdr_y_pos = (verdr_kolben.get_y() - (verdr_kolben.get_y() - verdr_kolben_start) *
                           (0.5 * (1 - np.cos(gesamte_frames[frame - 3 * phase_len]))))
            verdr_kolben.set_y(verdr_y_pos)
            phase_text.set_text('Isochoric Heat Output 4 → 1')

        stiel_start_y = kolben.get_y() + kolben_hoehe / 2
        stiel.set_ydata([stiel_start_y, 0])

        return kolben, verdr_kolben, stiel, phase_text

    ani = FuncAnimation(fig, update, frames=len(gesamte_frames), init_func=init, blit=True, interval=20)

    plt.show()


def joule_animation():
    # Basisparameter für das Rechteck
    left, right = 1, 4.5
    bottom, top = 1, 3
    diagonal_point = 1.75

    x = [left, left, right - 0.5, right - 0.5, right, right]
    y = [bottom, top, top, diagonal_point + 0.5, diagonal_point, bottom]

    # Parameter für das Trapez
    x1, x2 = 4, 4.5
    y1, y2, y3, y4 = 2.25, 2.3, 1.7, 1.8

    # Punkte, für Trapez
    x_trapez = [x1, x2, x2, x1, x1]
    y_trapez = [y1, y2, y3, y4, y1]

    # Initialisierung des Plots
    fig, ax = plt.subplots()
    ax.set_xlim(0, 5)
    ax.set_ylim(0, 4)
    ax.axis('off')

    # Rechteck zeichnen
    rect = plt.Polygon(np.column_stack([x, y]), closed=False, edgecolor='black', fill=None)
    ax.add_patch(rect)

    # Trapez zeichnen
    trapez = plt.Polygon(np.column_stack([x_trapez, y_trapez]), closed=True, edgecolor='black', facecolor='green')
    ax.add_patch(trapez)
    ax.text(x1 - 0.1, (y1 + y4) / 2, 'Turbine', verticalalignment='center', horizontalalignment='right')

    # Koordinaten des Kreises (mittig auf der linken Seite des Rechtecks)
    circle_x = left
    circle_y = (top + bottom) / 2
    circle_radius = 0.2

    # Kreis für Verdichter zeichnen
    circle = plt.Circle((circle_x, circle_y), circle_radius, edgecolor='black', facecolor='blue')
    ax.add_patch(circle)
    ax.text(circle_x + 0.25, circle_y, 'Compressor', verticalalignment='center')

    # Koordinaten des Rechtecks für die Brennkammer
    combustion_width = 0.5
    combustion_height = 0.3
    combustion_x = left + (right - left) / 2 - combustion_width / 2  # Anpassung der Position
    combustion_y = top - combustion_height / 2

    # Rechteck für die Brennkammer zeichnen
    combustion_rect = plt.Rectangle((combustion_x, combustion_y), combustion_width, combustion_height,
                                    edgecolor='black', facecolor='red')
    ax.add_patch(combustion_rect)
    ax.text(combustion_x + combustion_width / 2, combustion_y - 0.1, 'Combustion',
            verticalalignment='top', horizontalalignment='center')

    # Definition von zwei schrägen Linien, für den Verdichter
    line1_start = (0.85, 1.87)
    line1_end = (0.9, 2.17)
    line2_start = (1.15, 1.87)
    line2_end = (1.10, 2.17)

    # Zeichnen der schrägen Linien
    plt.plot([line1_start[0], line1_end[0]], [line1_start[1], line1_end[1]], 'k-')
    plt.plot([line2_start[0], line2_end[0]], [line2_start[1], line2_end[1]], 'k-')

    # Initialisierung des Punkts
    point, = plt.plot([], [], 'ro')

    # Erzeugung der Pfade für die Animation
    path_x, path_y = [], []
    num_points = 100  # Anzahl der Zwischenpunkte zwischen den Eckpunkten

    # Generiere Pfad entlang der Kanten des Rechtecks im Uhrzeigersinn
    for i in range(len(x) - 1):
        temp_x = np.linspace(x[i], x[i + 1], num_points, endpoint=False)
        temp_y = np.linspace(y[i], y[i + 1], num_points, endpoint=False)
        path_x.extend(temp_x)
        path_y.extend(temp_y)

    # Zusätzliche Punkte am Ende hinzu
    extend_x = np.linspace(right, right + 0.5, num_points)
    extend_y = np.full(num_points, bottom)
    path_x.extend(extend_x)
    path_y.extend(extend_y)

    def update(frame):
        point.set_data([path_x[frame % len(path_x)]], [path_y[frame % len(path_y)]])
        return point,

    # Animation erstellen
    ani = FuncAnimation(fig, update, frames=len(path_x), interval=20, blit=True)

    plt.show()


def show_diagrams_and_animation():
    if not are_fields_filled():
        return
    show_diagrams()  # Zeige Pv- und Ts-Diagramme
    selection = process_combobox.get()
    if selection == "Otto":
        otto_animation()  # Zeige Animation in einem neuen Fenster
    elif selection == "Diesel":
        diesel_animation()
    elif selection == "Stirling":
        stirling_animation()
    elif selection == "Joule":
        joule_animation()


# Prozessgrößen ein- und ausblenden
process_frames_visible = False


def clear_all_fields():
    for frame in [state1_frame, state2_frame, state3_frame, state4_frame] + process_frames:
        frame.clear_fields()
    compression_ratio_entry.delete(0, tk.END)
    heat_or_injection_entry.delete(0, tk.END)
    # Wirkungsgrad-Entry leeren
    efficiency_entry.config(state='normal')
    efficiency_entry.delete(0, tk.END)
    efficiency_entry.config(state='readonly')
    state_history.clear()


def toggle_process_frames():
    global process_frames_visible
    process_frames_visible = not process_frames_visible
    for frame in process_frames:
        frame.toggle_content()  # Rufen Sie die neue Methode auf, um den Inhalt zu toggeln
    toggle_button.config(text="Hide Process Values" if process_frames_visible else "Show Process Values")


def show_instructions():
    instructions = (
        "Welcome to the Calculation Tool for Thermodynamic Cycles!\n\n"
        "Instructions:\n"
        "- Select the thermodynamic cycle and the working medium.\n"
        "- Enter the required data into the fields.\n"
        "- Use the 'Calculate' button to perform the calculations.\n"
        "- Use the 'Clear Fields' button to reset the input fields.\n"
        "- 'Show Diagrams and Animation' displays the resulting diagrams and animations.\n\n"
        "Enjoy and successful calculations!"
    )
    messagebox.showinfo("Instructions", instructions)


# Hauptfenster erstellen
root = tk.Tk()
root.title("Calculation Tool for Thermodynamic Cycles")

# Bildschirmgröße abrufen
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Fenstergröße festlegen
window_width = 1150
window_height = 600

# Fensterposition berechnen
x_position = (screen_width - window_width) // 2
y_position = (screen_height - window_height) // 2

# Fensterposition setzen
root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

# Grid-Konfiguration im Hauptfenster für 3x3-Layout
for i in range(3):
    root.grid_rowconfigure(i, weight=1)
    root.grid_columnconfigure(i, weight=1)

# Frames für jeden Zustand erstellen
state1_frame = StateFrame(root, "State 1", 0, 0, first_state=True)  # Oben links
state2_frame = StateFrame(root, "State 2", 0, 2)  # Oben rechts
state3_frame = StateFrame(root, "State 3", 2, 2)  # Unten rechts
state4_frame = StateFrame(root, "State 4", 2, 0)  # Unten links

process_frames = [
    ProcessFrame(root, "", 0, 1),
    ProcessFrame(root, "", 1, 2),
    ProcessFrame(root, "", 2, 1),
    ProcessFrame(root, "", 1, 0)
]

# Button-Frame erstellen
button_frame = tk.Frame(root)
button_frame.grid(row=2, column=3, padx=5, pady=5, sticky="nsew")
# Button, der die Berechnungen durchführt, zum Button-Frame hinzufügen
berechnen_button = tk.Button(button_frame, text="Calculate", font=("Arial", 12, "bold"),
                             command=perform_calculations)
berechnen_button.pack(fill="x", padx=5, pady=2)
# Button zum Löschen der Felder
clear_button = tk.Button(button_frame, text="Clear Fields", command=clear_all_fields)
clear_button.pack(fill="x", padx=5, pady=2)
# Button für Diagramme und Animation anzeigen
diagrams_button = tk.Button(button_frame, text="Show Diagrams and animation", command=show_diagrams_and_animation)
diagrams_button.pack(fill="x", padx=5, pady=2)
# Button zum Umschalten der Prozesswerte-Anzeige
toggle_button = tk.Button(button_frame, text="Show Process Values", command=toggle_process_frames)
toggle_button.pack(fill="x", padx=5, pady=2)


# Frames erstellen für Auswahl der Kreisprozesse und Eingabe der Ausgangsdaten
process_combobox_frame = tk.Frame(root)
process_combobox_frame.grid(row=0, column=3, padx=5, pady=5, sticky="n")
# Label im Frame hinzufügen
process_selection_label = tk.Label(process_combobox_frame, text="Choose Thermodynamic Cycle:",
                                   font=("Arial", 13, "bold"))
process_selection_label.pack(side="top", fill="x")


# Combobox im Frame hinzufügen
process_combobox = ttk.Combobox(process_combobox_frame, values=['Otto', 'Diesel', 'Stirling', 'Joule'],
                                state='readonly')
process_combobox.pack(side="top", fill="x")
process_combobox.set('Otto')  # Setzt "Otto" als Standardauswahl
# Zusätzliche Entry-Felder erstellen
compression_ratio_label = tk.Label(process_combobox_frame)
compression_ratio_label.pack(side="top", fill="x")
compression_ratio_entry = tk.Entry(process_combobox_frame)
compression_ratio_entry.pack(side="top", fill="x")
heat_or_injection_label = tk.Label(process_combobox_frame)
heat_or_injection_label.pack(side="top", fill="x")
heat_or_injection_entry = tk.Entry(process_combobox_frame)
heat_or_injection_entry.pack(side="top", fill="x")


# Frame für das Medium und die Eigenschaften erstellen
medium_frame = tk.Frame(root)
medium_frame.grid(row=1, column=3, padx=5, pady=5, sticky="n")
# Label und Combobox für die Mediumauswahl
medium_label = tk.Label(medium_frame, text="Choose Gas:", font=("Arial", 13, "bold"))
medium_label.pack(side="top", fill="x")
medium_combobox = ttk.Combobox(medium_frame, values=['Air', 'Hydrogen', 'Nitrogen', 'Helium', 'Custom'],
                               state='readonly')
medium_combobox.pack(side="top", fill="x", pady=(5, 10))
medium_combobox.set('Air')  # Setzt "Air" als Standardauswahl


# Frame für den Wirkungsgrad
efficiency_frame = tk.Frame(root)  # oder verwenden Sie medium_frame, falls es im gleichen Abschnitt sein soll
efficiency_frame.grid(row=1, column=1, columnspan=1, sticky="",
                      padx=5, pady=10)    # Anpassung der Grid-Position nach Bedarf
# Label für den Wirkungsgrad
efficiency_label = tk.Label(efficiency_frame, text="Efficiency (%):", font=("Arial", 13, "bold"))
efficiency_label.pack(side="top")
# Entry-Feld für den Wirkungsgrad
custom_font = tkfont.Font(family="Arial", size=10, weight= "bold")
efficiency_entry = tk.Entry(efficiency_frame, font=custom_font)
efficiency_entry.pack(side="left", fill="x", expand=True)
efficiency_entry.config(state='readonly')


# Entryfelder und Labels für Cp, Cv und k
properties = ['Cp (J/kg·K):', 'Cv (J/kg·K):', 'k (-):']
entries = []

for prop in properties:
    # Erstelle ein Frame für jedes Label-Entry-Paar
    pair_frame = tk.Frame(medium_frame)
    pair_frame.pack(side="top", fill="x", pady=(0, 10))

    # Label links vom Entry-Feld
    prop_label = tk.Label(pair_frame, text=prop)
    prop_label.pack(side="left")

    # Entry-Feld rechts vom Label
    prop_entry = tk.Entry(pair_frame)
    prop_entry.pack(side="left", fill="x", expand=True)
    entries.append(prop_entry)

# Pfeile zwischen den Zuständen hinzufügen
# Hinweis: Die Implementierung der Pfeile kann variieren (z.B. als Bilder oder gezeichnete Linien)
arrow1 = tk.Label(root, text="→", font=("Arial", 30))
arrow1.grid(row=1, column=1, sticky="n")

arrow2 = tk.Label(root, text="↓", font=("Arial", 30))
arrow2.grid(row=1, column=1, sticky="e")

arrow3 = tk.Label(root, text="←", font=("Arial", 30))
arrow3.grid(row=1, column=1, sticky="s")

arrow4 = tk.Label(root, text="↑", font=("Arial", 30))
arrow4.grid(row=1, column=1, sticky="w")


# Funktion zum Aktualisieren der Zustandsänderungs-Labels
def update_process_labels(event):
    process_changes = {
        'Otto': ["Isentropic Compression", "Isochoric Heat Input", "Isentropic Expansion", "Isochoric Heat Output"],
        'Diesel': ["Isentropic Compression", "Isobaric Heat Input", "Isentropic Expansion", "Isochoric Heat Output"],
        'Stirling': ["Isothermal Compression", "Isochoric Heat Input", "Isothermal Expansion", "Isochoric Heat Output"],
        'Joule': ["Isentropic Compression", "Isobaric Heat Input", "Isentropic Expansion", "Isobaric Heat Output"]
    }
    process = process_combobox.get()
    if process in process_changes:
        for frame, title in zip(process_frames, process_changes[process]):
            frame.update_title(title)

    selection = process_combobox.get()
    if selection == "Otto" or selection == "Stirling":
        compression_ratio_label.config(text="Compression Ratio [v1/v2]")
        heat_or_injection_label.config(text="Heat Transfer [kJ/kg]")
    elif selection == "Joule":
        compression_ratio_label.config(text="Pressure Ratio [p2/p1]")
        heat_or_injection_label.config(text="Heat Transfer [kJ/kg]")
    elif selection == "Diesel":
        compression_ratio_label.config(text="Compression Ratio [v1/v2]")
        heat_or_injection_label.config(text="Injection Ratio [T3/T2]")

    clear_all_fields()


update_process_labels(None)


# Event-Bindung für die Combobox
process_combobox.bind('<<ComboboxSelected>>', update_process_labels)

# Aktualisierung der spezifischen Konstanten bei Auswahl
def update_properties(initial=False):
    media_properties = {
        'Air': {'cp': 1005, 'cv': 718, 'k': 1.4},
        'Hydrogen': {'cp': 14304, 'cv': 10153, 'k': 1.41},
        'Nitrogen': {'cp': 1040, 'cv': 743, 'k': 1.4},
        'Helium': {'cp': 5193, 'cv': 3116, 'k': 1.66},
        'Custom': {'cp': '', 'cv': '', 'k': ''}
    }

    selected_medium = medium_combobox.get()
    properties = media_properties.get(selected_medium, {'cp': '', 'cv': '', 'k': ''})

    for i, key in enumerate(['cp', 'cv', 'k']):
        entries[i].config(state='normal')
        entries[i].delete(0, tk.END)
        entries[i].insert(0, str(properties[key]))
        if selected_medium == 'Custom':
            entries[i].config(state='normal')
        else:
            entries[i].config(state='readonly')


# Initialwerte laden
update_properties(initial=True)


# Event-Bindung für die Combobox
medium_combobox.bind('<<ComboboxSelected>>', lambda event: update_properties())

root.after(100, show_instructions)  # 100 ms nach Fensteraktivierung

root.mainloop()

