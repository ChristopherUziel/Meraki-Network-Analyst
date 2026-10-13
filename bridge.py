import queue
import shutil
import subprocess
import threading
import time
import tkinter as tk
import urllib.request
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

import uvicorn

from app.main import app

API_HOST = "127.0.0.1"
API_PORT = 8000
API_HEALTH_URL = f"http://{API_HOST}:{API_PORT}/health"

TUNNEL_ID = "meraki-network-analyst"
TUNNEL_URL = "https://tkfvsm4p-8000.usw3.devtunnels.ms"


class MerakiCopilotBridge:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Meraki Copilot")
        self.root.geometry("720x500")
        self.root.minsize(650, 430)

        self.uvicorn_server: uvicorn.Server | None = None
        self.api_thread: threading.Thread | None = None
        self.tunnel_process: subprocess.Popen[str] | None = None

        self.log_queue: queue.Queue[str] = queue.Queue()
        self.is_starting = False
        self.is_stopping = False

        self.api_status = tk.StringVar(value="Detenida")
        self.tunnel_status = tk.StringVar(value="Detenido")
        self.url_status = tk.StringVar(value=TUNNEL_URL)

        self._build_interface()
        self._process_log_queue()

        self.root.protocol("WM_DELETE_WINDOW", self.close_application)

    def _build_interface(self) -> None:
        title = tk.Label(
            self.root,
            text="Meraki Copilot",
            font=("Segoe UI", 18, "bold"),
        )
        title.pack(pady=(20, 15))

        status_frame = tk.Frame(self.root)
        status_frame.pack(fill="x", padx=25)

        tk.Label(
            status_frame,
            text="API local:",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
            width=18,
        ).grid(row=0, column=0, sticky="w", pady=4)

        tk.Label(
            status_frame,
            textvariable=self.api_status,
            font=("Segoe UI", 10),
            anchor="w",
        ).grid(row=0, column=1, sticky="w", pady=4)

        tk.Label(
            status_frame,
            text="Dev Tunnel:",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
            width=18,
        ).grid(row=1, column=0, sticky="w", pady=4)

        tk.Label(
            status_frame,
            textvariable=self.tunnel_status,
            font=("Segoe UI", 10),
            anchor="w",
        ).grid(row=1, column=1, sticky="w", pady=4)

        tk.Label(
            status_frame,
            text="URL pública:",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
            width=18,
        ).grid(row=2, column=0, sticky="w", pady=4)

        url_label = tk.Label(
            status_frame,
            textvariable=self.url_status,
            font=("Segoe UI", 10),
            fg="#0067c0",
            cursor="hand2",
            anchor="w",
        )
        url_label.grid(row=2, column=1, sticky="w", pady=4)
        url_label.bind("<Button-1>", self.copy_url)

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)

        self.start_button = tk.Button(
            button_frame,
            text="Iniciar",
            width=15,
            height=2,
            command=self.start_services,
        )
        self.start_button.grid(row=0, column=0, padx=8)

        self.stop_button = tk.Button(
            button_frame,
            text="Detener",
            width=15,
            height=2,
            state="disabled",
            command=self.stop_services,
        )
        self.stop_button.grid(row=0, column=1, padx=8)

        self.copy_button = tk.Button(
            button_frame,
            text="Copiar URL",
            width=15,
            height=2,
            command=self.copy_url,
        )
        self.copy_button.grid(row=0, column=2, padx=8)

        tk.Label(
            self.root,
            text="Registro",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        ).pack(fill="x", padx=25)

        self.log_text = ScrolledText(
            self.root,
            height=14,
            state="disabled",
            font=("Consolas", 9),
        )
        self.log_text.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=(5, 20),
        )

        self.write_log("Bridge listo. Presiona Iniciar.")

    def write_log(self, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.log_queue.put(f"[{timestamp}] {message}")

    def _process_log_queue(self) -> None:
        try:
            while True:
                message = self.log_queue.get_nowait()

                self.log_text.configure(state="normal")
                self.log_text.insert("end", message + "\n")
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except queue.Empty:
            pass

        self.root.after(100, self._process_log_queue)

    def start_services(self) -> None:
        if self.is_starting:
            return

        self.is_starting = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="disabled")

        worker = threading.Thread(
            target=self._start_services_worker,
            daemon=True,
        )
        worker.start()

    def _start_services_worker(self) -> None:
        try:
            devtunnel_path = shutil.which("devtunnel")

            if not devtunnel_path:
                raise RuntimeError("No se encontró devtunnel en el PATH de Windows.")

            self.write_log("Iniciando API local...")
            self.root.after(
                0,
                lambda: self.api_status.set("Iniciando..."),
            )

            config = uvicorn.Config(
                app=app,
                host=API_HOST,
                port=API_PORT,
                log_level="info",
                access_log=False,
            )

            self.uvicorn_server = uvicorn.Server(config)

            self.api_thread = threading.Thread(
                target=self.uvicorn_server.run,
                daemon=True,
            )
            self.api_thread.start()

            if not self._wait_for_api():
                raise RuntimeError(
                    "La API local no respondió dentro del tiempo esperado."
                )

            self.root.after(
                0,
                lambda: self.api_status.set("Activa"),
            )
            self.write_log(f"API activa en http://{API_HOST}:{API_PORT}")

            self.write_log(f"Iniciando túnel persistente: {TUNNEL_ID}")
            self.root.after(
                0,
                lambda: self.tunnel_status.set("Iniciando..."),
            )

            creation_flags = subprocess.CREATE_NO_WINDOW

            self.tunnel_process = subprocess.Popen(
                [
                    devtunnel_path,
                    "host",
                    TUNNEL_ID,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=creation_flags,
            )

            tunnel_log_thread = threading.Thread(
                target=self._read_tunnel_output,
                daemon=True,
            )
            tunnel_log_thread.start()

            time.sleep(3)

            if self.tunnel_process.poll() is not None:
                raise RuntimeError("Dev Tunnel terminó inesperadamente.")

            self.root.after(
                0,
                lambda: self.tunnel_status.set("Activo"),
            )
            self.write_log(f"Túnel activo: {TUNNEL_URL}")
            self.write_log("El agente de Copilot ya puede usar la API.")

            self.root.after(
                0,
                lambda: self.stop_button.configure(state="normal"),
            )

        except Exception as error:
            self.write_log(f"Error al iniciar: {error}")

            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "Error de inicio",
                    str(error),
                ),
            )

            self._stop_services_internal()

            self.root.after(
                0,
                lambda: self.start_button.configure(state="normal"),
            )

        finally:
            self.is_starting = False

    def _wait_for_api(self, attempts: int = 20) -> bool:
        for _ in range(attempts):
            try:
                with urllib.request.urlopen(
                    API_HEALTH_URL,
                    timeout=1,
                ) as response:
                    if response.status == 200:
                        return True
            except Exception:
                time.sleep(0.5)

        return False

    def _read_tunnel_output(self) -> None:
        process = self.tunnel_process

        if process is None or process.stdout is None:
            return

        for line in process.stdout:
            clean_line = line.strip()

            if clean_line:
                self.write_log(f"Dev Tunnel: {clean_line}")

    def stop_services(self) -> None:
        if self.is_stopping:
            return

        self.is_stopping = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="disabled")

        worker = threading.Thread(
            target=self._stop_services_worker,
            daemon=True,
        )
        worker.start()

    def _stop_services_worker(self) -> None:
        self.write_log("Deteniendo servicios...")
        self._stop_services_internal()

        self.root.after(
            0,
            lambda: self.start_button.configure(state="normal"),
        )
        self.root.after(
            0,
            lambda: self.stop_button.configure(state="disabled"),
        )

        self.write_log("Servicios detenidos.")
        self.is_stopping = False

    def _stop_services_internal(self) -> None:
        if self.tunnel_process is not None:
            if self.tunnel_process.poll() is None:
                self.tunnel_process.terminate()

                try:
                    self.tunnel_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.tunnel_process.kill()

            self.tunnel_process = None

        if self.uvicorn_server is not None:
            self.uvicorn_server.should_exit = True

        if self.api_thread is not None and self.api_thread.is_alive():
            self.api_thread.join(timeout=5)

        self.uvicorn_server = None
        self.api_thread = None

        self.root.after(
            0,
            lambda: self.api_status.set("Detenida"),
        )
        self.root.after(
            0,
            lambda: self.tunnel_status.set("Detenido"),
        )

    def copy_url(self, event: object | None = None) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(TUNNEL_URL)
        self.root.update()

        self.write_log("URL pública copiada al portapapeles.")

    def close_application(self) -> None:
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="disabled")

        self.write_log("Cerrando aplicación...")

        worker = threading.Thread(
            target=self._close_application_worker,
            daemon=True,
        )
        worker.start()

    def _close_application_worker(self) -> None:
        self._stop_services_internal()
        self.root.after(0, self.root.destroy)


def main() -> None:
    root = tk.Tk()
    MerakiCopilotBridge(root)
    root.mainloop()


if __name__ == "__main__":
    main()
