import tkinter as tk
from tkinter import messagebox

# Dicionário com as velocidades
velocidades = {
    1: 3.6,  # Andando
    2: 6,    # Cavalo
    3: 15,   # Trotando
    4: 20,   # Meio Galope
    5: 55    # Galopando
}

def calcular_viagem():
    try:
        distancia = float(distancia_entry.get())
        modo_viagem = int(modo_viagem_entry.get())
        horas_dia = float(horas_dia_entry.get())

        if horas_dia > 24:
            messagebox.showinfo("Erro", "Não é possível viajar mais de 24 horas por dia.")
            return

        if modo_viagem not in velocidades:
            messagebox.showinfo("Erro", "Modo de viagem inválido.")
        else:
            distancia_dia = velocidades[modo_viagem] * horas_dia
            dias = distancia / distancia_dia
            messagebox.showinfo("Resultado", f"Sua viagem levará aproximadamente {dias} dias.")
    except ValueError:
        messagebox.showinfo("Erro", "Digite valores válidos.")

root = tk.Tk()

tk.Label(root, text="Distância da viagem em km: ").grid(row=0)
distancia_entry = tk.Entry(root)
distancia_entry.grid(row=0, column=1)

tk.Label(root, text="Modo de viagem (1-Andando, 2-Cavalo, 3-Trotando, 4-Meio Galope, 5-Galopando): ").grid(row=1)
modo_viagem_entry = tk.Entry(root)
modo_viagem_entry.grid(row=1, column=1)

tk.Label(root, text="Horas por dia que você viajará (até 24 horas): ").grid(row=2)
horas_dia_entry = tk.Entry(root)
horas_dia_entry.grid(row=2, column=1)

tk.Button(root, text="Calcular", command=calcular_viagem).grid(row=3, column=1)

root.mainloop()
