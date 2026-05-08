import customtkinter as ctk
from tkinter import filedialog, messagebox
import yt_dlp
import os
import threading
import json
from pathlib import Path

class MusicDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Downloader")
        self.geometry("900x800")
        ctk.set_appearance_mode("dark")
        
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.base_path, "config.json")
        self.is_downloading = False
        self.stop_requested = False
        
        saved_path = self.load_config()
        self.download_folder = ctk.StringVar(value=saved_path)
        
        self.create_widgets()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f).get("path", str(Path.home() / "Downloads"))
            except: pass
        return str(Path.home() / "Downloads")

    def save_config(self, path):
        with open(self.config_file, "w") as f:
            json.dump({"path": path}, f)

    def log(self, message, color="#ffffff"):
        """Escribe en la consola con el color indicado"""
        self.console.configure(state="normal")
        tag_name = f"color_{color.replace('#', '')}"
        self.console.tag_config(tag_name, foreground=color)
        self.console.insert("end", f"> {message}\n", tag_name)
        self.console.see("end")
        self.console.configure(state="disabled")

    def create_widgets(self):
        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main, text="Downloader - Descarga tu musica", font=("Arial", 22, "bold")).pack(pady=10)

        # Selector de Carpeta
        f_frame = ctk.CTkFrame(main)
        f_frame.pack(fill="x", pady=5)
        ctk.CTkEntry(f_frame, textvariable=self.download_folder).pack(side="left", fill="x", expand=True, padx=5)
        
        def select_folder():
            path = filedialog.askdirectory()
            if path:
                self.download_folder.set(path)
                self.save_config(path)

        ctk.CTkButton(f_frame, text="Carpeta", width=80, command=select_folder).pack(side="right", padx=5)

        # Entrada de canciones
        self.songs_textbox = ctk.CTkTextbox(main, height=250)
        self.songs_textbox.pack(fill="both", expand=True, padx=10, pady=10)

        # Botones
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)

        self.btn_start = ctk.CTkButton(btn_frame, text="Iniciar Descarga", command=self.start, fg_color="#1f6aa5")
        self.btn_start.pack(side="left", fill="x", expand=True, padx=5)

        self.btn_stop = ctk.CTkButton(btn_frame, text="Cancelar", command=self.stop, fg_color="#c0392b", state="disabled")
        self.btn_stop.pack(side="right", fill="x", expand=True, padx=5)

        # Consola
        self.console = ctk.CTkTextbox(main, height=200, state="disabled", fg_color="#1a1a1a")
        self.console.pack(fill="both", expand=True, padx=10, pady=10)

    def stop(self):
        self.stop_requested = True
        self.log("⏹️ Cancelando proceso...", "#f1c40f")

    def start(self):
        if self.is_downloading: return
        content = self.songs_textbox.get("1.0", "end").strip()
        items = [s.strip() for s in content.split("\n") if s.strip()]
        
        if not items:
            messagebox.showwarning("Error", "La lista está vacía")
            return
        
        self.is_downloading = True
        self.stop_requested = False
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        threading.Thread(target=self.download, args=(items,), daemon=True).start()

    def download(self, items):
        ffmpeg_exe = os.path.join(self.base_path, "ffmpeg.exe")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{self.download_folder.get()}/%(title)s.%(ext)s',
            'ffmpeg_location': ffmpeg_exe,
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for index, item in enumerate(items, start=1):
                if self.stop_requested: break
                
                self.btn_start.configure(text=f"Procesando {index}/{len(items)}...")
                
                # 1. Buscando (Texto en Blanco)
                self.log(f"Descargando: {item}", "#ffffff")
                
                query = item if "youtube.com/" in item or "youtu.be/" in item else f"ytsearch1:{item}"
                
                try:
                    # Intentar descarga
                    error_code = ydl.download([query])
                    
                    if error_code == 0:
                        # 2. Éxito (Texto en Verde)
                        self.log(f"Hecho: {item}", "#2ecc71")
                    else:
                        # 3. Error (Texto en Rojo)
                        self.log(f"Error al descargar: {item}", "#e74c3c")
                except:
                    self.log(f"Error crítico: {item}", "#e74c3c")

        # Mensaje Final en Verde
        self.log("--- PROCESO FINALIZADO ---", "#2ecc71")
        self.is_downloading = False
        self.btn_start.configure(state="normal", text="Iniciar Descarga")
        self.btn_stop.configure(state="disabled")

if __name__ == "__main__":
    app = MusicDownloaderApp()
    app.mainloop()