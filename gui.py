import tkinter as tk

def toggle_suit():
    global suit_on
    suit_on = not suit_on
    status_label.config(text=f"スーツ着用: {'ON' if suit_on else 'OFF'}")

suit_on = False
root = tk.Tk()
root.title("Virtual Suit Controller")

toggle_button = tk.Button(root, text="スーツ切替", command=toggle_suit)
toggle_button.pack(pady=20)

status_label = tk.Label(root, text="スーツ着用: OFF")
status_label.pack()

root.mainloop()
