import os
import cv2
import tkinter as tk
import uuid
import subprocess
import shutil
import time
import threading
import queue
import multiprocessing as mp
from multiprocessing.queues import Queue as MpQueue
from multiprocessing.synchronize import Event as MpEvent
from cv2.typing import MatLike
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
from filters import *
from filters import ALL_FILTERS
from typing import List, Callable, Any, Dict
from params_defs import PARAMS_DEFS


PADX = 10
PADY = 5
VIDEO_EXTENSIONS = (".mp4", ".avi")
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg")
FilterFn = Callable[..., MatLike]

def filter_process_loop(
    frame_queue: MpQueue,
    render_queue: MpQueue,
    ctrl_queue: MpQueue,
    stop_event: MpEvent
) -> None:
    from filters import ALL_FILTERS

    filters_map = {func.__name__: func for func in ALL_FILTERS}

    filter_name = "original"
    params: Dict[str, int] = {}
    preview_max: tuple[int, int] | None = None

    while not stop_event.is_set():
        while True:
            try:
                msg = ctrl_queue.get_nowait()
            except queue.Empty:
                break

            msg_type = msg.get("type")
            if msg_type == "update_filter":
                filter_name = msg.get("filter_name", "original")
                params = dict(msg.get("params", {}))
            elif msg_type == "update_preview":
                preview_max = msg.get("preview_max")
            elif msg_type == "stop":
                stop_event.set()
                break

        try:
            frame = frame_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        if preview_max:
            max_w, max_h = preview_max
            h, w = frame.shape[:2]
            if max_w > 1 and max_h > 1:
                scale = min(max_w / w, max_h / h)
                if scale > 0:
                    new_w = max(1, int(w * scale))
                    new_h = max(1, int(h * scale))
                    if new_w != w or new_h != h:
                        frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

        filter_fn = filters_map.get(filter_name, original)
        if params:
            filtered = filter_fn(frame, **params)
        else:
            filtered = filter_fn(frame)

        try:
            render_queue.put_nowait(filtered)
        except queue.Full:
            # drop frame on overload
            pass


class Filters:
    def __init__(self):
        self.selected = []

        # region ----|1|---- Filter Params
        self._params_defs = PARAMS_DEFS
        self.params = {}

        for filter_name in self._params_defs.keys():
            param_registry = self._params_defs.get(filter_name, {})
            self.params.setdefault(filter_name, {})
            for param_name, cfg in param_registry.items():
                self.params[filter_name][param_name] = cfg.default
        # endregion -|1|-

        # region ----|1|---- Define filters
        self.filters: List[Callable] = ALL_FILTERS
        self.t_filters: List[Callable] = ()
        'Filters that work only with time'
        # endregion -|1|-

        # region ----|1|---- Map filters
        self.filters_map: dict[str, FilterFn] = {
            func.__name__: func
            for func in self.filters
        }
        self.t_filters_map: dict[str, FilterFn] = {
            func.__name__: func
            for func in self.t_filters
        }
        self.all_filters_map: dict[str, FilterFn] = self.filters_map | self.t_filters_map
        # endregion -|1|-

    def set_param(
            self,
            filter_name: str,
            param: str,
            value: int,
            frame: MatLike | None
        ) -> None:

        cfg = self._params_defs[filter_name][param]

        def resolve(v):
            if callable(v):
                if frame is None:
                    return None
                return v(frame)
            return v

        min_v = resolve(cfg.min)
        max_v = resolve(cfg.max)

        if min_v is None or max_v is None:
            self.params[filter_name][param] = value
        else:
            self.params[filter_name][param] = max(min_v, min(max_v, value))

    def apply_filter(self, frame: MatLike, filter_str: str) -> MatLike:
        filter_fn = self.all_filters_map[filter_str]
        kwargs = self.params.get(filter_str)
        if kwargs:
            frame = filter_fn(frame, **kwargs)
        else:
            frame = filter_fn(frame)

        return frame


class Midia:

    def __init__(self):
        self.path = ""
        self.file_ext = ""
        self.cap: cv2.VideoCapture | None = None
        self.image_layers = []
        self.playing = False
        self.fps = 0.0
        self.raw_queue: MpQueue | None = None
        self.render_queue: MpQueue | None = None
        self.ctrl_queue: MpQueue | None = None
        self.stop_event: MpEvent | None = None
        self.reader_thread: threading.Thread | None = None
        self.filter_process: mp.Process | None = None
        self.filter_lock = threading.Lock()
        self.current_filter: str = "original"
        self.current_params: Dict[str, int] = {}
        self.last_frame: MatLike | None = None
        self.last_render_frame: MatLike | None = None
        self.preview_max: tuple[int, int] | None = None
        self.last_preview_sent: tuple[int, int] | None = None

    @property
    def frame_time(self):
        return 1.0 / self.fps if self.fps > 0 else 1.0 / 30.0

    def _reader_loop(self):
        next_frame_time = time.perf_counter()
        while self.stop_event and not self.stop_event.is_set() and self.cap:
            now = time.perf_counter()
            if now < next_frame_time:
                time.sleep(max(0.0, next_frame_time - now))
                continue

            ret, frame = self.cap.read()

            if not ret:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                next_frame_time = time.perf_counter()
                continue

            with self.filter_lock:
                self.last_frame = frame

            try:
                if self.raw_queue:
                    self.raw_queue.put_nowait(frame)
            except queue.Full:
                # drop frame on overload
                pass

            next_frame_time += self.frame_time

    def start_video_pipeline(self, filters: Filters):
        self.stop_video_pipeline()

        # reset queues
        with self.filter_lock:
            self.current_filter = filters.selected[0] if filters.selected else "original"
            self.current_params = dict(filters.params.get(self.current_filter, {}))
            self.last_frame = None

        ctx = mp.get_context("spawn")
        self.raw_queue = ctx.Queue(maxsize=10)
        self.render_queue = ctx.Queue(maxsize=10)
        self.ctrl_queue = ctx.Queue()
        self.stop_event = ctx.Event()

        self.reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.filter_process = ctx.Process(
            target=filter_process_loop,
            args=(self.raw_queue, self.render_queue, self.ctrl_queue, self.stop_event),
            daemon=True
        )
        self.reader_thread.start()
        self.filter_process.start()

        if self.ctrl_queue:
            self.ctrl_queue.put({
                "type": "update_filter",
                "filter_name": self.current_filter,
                "params": dict(self.current_params)
            })

    def stop_video_pipeline(self):
        if self.stop_event:
            self.stop_event.set()

        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=0.5)
        if self.filter_process and self.filter_process.is_alive():
            try:
                if self.ctrl_queue:
                    self.ctrl_queue.put({"type": "stop"})
            except Exception:
                pass
            self.filter_process.join(timeout=0.5)

    def update_filter(self, filter_name: str, params: Dict[str, int]):
        with self.filter_lock:
            self.current_filter = filter_name
            self.current_params = dict(params)

        # clear queues to show new filter immediately
        self._drain_queue(self.raw_queue)
        self._drain_queue(self.render_queue)
        self._drain_queue(self.ctrl_queue)

        if self.ctrl_queue:
            try:
                self.ctrl_queue.put({
                    "type": "update_filter",
                    "filter_name": filter_name,
                    "params": dict(params)
                })
            except Exception:
                pass

    def update_preview_max(self, max_w: int, max_h: int):
        with self.filter_lock:
            self.preview_max = (max_w, max_h)
        if self.ctrl_queue and (max_w, max_h) != self.last_preview_sent:
            try:
                self.ctrl_queue.put({
                    "type": "update_preview",
                    "preview_max": (max_w, max_h)
                })
                self.last_preview_sent = (max_w, max_h)
            except Exception:
                pass

    def _drain_queue(self, q):
        if q is None:
            return
        while True:
            try:
                q.get_nowait()
            except Exception:
                break

    def mux_audio(
        self,
        video_no_audio: str, # path
        original_video: str, # path
        output_path: str # path
    ) -> None:
        if not shutil.which("ffmpeg"):
            raise FileNotFoundError("ffmpeg not found in PATH")

        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_no_audio,
            "-i", original_video,
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            output_path
        ]

        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def save_image(self, filters: Filters):
        path = filedialog.asksaveasfilename(
            title="Salvar imagem",
            defaultextension=".png",
            initialfile=f"{uuid.uuid4().hex}.png",
            filetypes=[
                ("PNG", "*.png"),
                ("JPEG", "*.jpg"),
                ("Todos os arquivos", "*.*")
            ]
        )

        if not path:
            return

        img = self.image_layers[0][1]
        if filters.selected:
            filt = filters.selected[0]
            img = filters.apply_filter(img, filt)
        cv2.imwrite(path, img)

        messagebox.showinfo("Save", "Image Saved Successfully!")

    def save_video(self, filters: Filters):
        fourcc = cv2.VideoWriter_fourcc('m','p','4','v')

        output_path = filedialog.asksaveasfilename(
            title="salvar video",
            defaultextension=".mp4",
            initialfile=f"{uuid.uuid4().hex}.mp4",
            filetypes=[
                ("MP4", "*.mp4"),
                ("AVI", "*.avi")
            ]
        )

        if not output_path:
            return

        temp_path = f"{uuid.uuid4().hex}.mp4"

        cap = cv2.VideoCapture(self.path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        fps = fps if fps > 0 else 30
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        writer = cv2.VideoWriter(
            filename=temp_path,
            fourcc=fourcc,
            fps=fps,
            frameSize=(w, h)
        )

        filter_name = self.current_filter
        params = dict(self.current_params)
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            filter_fn = original
            if filter_name:
                filter_fn = filters.all_filters_map.get(filter_name, original)

            if params:
                frame = filter_fn(frame, **params)
            else:
                frame = filter_fn(frame)

            writer.write(frame)

        writer.release()
        cap.release()

        try:
            self.mux_audio(
                video_no_audio=temp_path,
                original_video=self.path,
                output_path=output_path
            )
        except FileNotFoundError:
            messagebox.showerror(
                "ffmpeg not found",
                "ffmpeg nao esta instalado ou nao esta no PATH. O video foi salvo sem audio."
            )
            os.replace(temp_path, output_path)
            return
        except Exception as exc:
            messagebox.showerror(
                "Save error",
                f"Falha ao muxar audio: {exc}"
            )
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return

        # Delete temporary path
        if os.path.exists(temp_path):
            os.remove(temp_path)

        messagebox.showinfo("Save", "Video Saved Successfully!")


class GUI:
    def __init__(self, filters: Filters, midia: Midia):
        # region ----|1|---- GUI Start
        self.root = tk.Tk()
        self.root.title("Midiafilt")
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.width = int(screen_w * 0.8)
        self.height = int(screen_h * 0.8)
        self.x = (screen_w - self.width) // 2
        self.y = ((screen_h - self.height) // 2) // 2
        self.root.geometry(f"{self.width}x{self.height}+{self.x}+{self.y}")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.FILTER_COLUMN_WIDTH = 0.15 * self.width
        self.filters = filters
        self.midia = midia
        self.frame_counter = 0
        self.next_frame_time = 0.0
        # endregion -|1|-

        # region ----|1|---- Root Grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=0)
        self.root.grid_columnconfigure(2, weight=0, minsize=self.FILTER_COLUMN_WIDTH)

        self.left_frame = tk.Frame(self.root)
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        self.left_frame.grid_rowconfigure(0, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)

        self.divider1 = tk.Frame(self.root, width=2, bg="gray")
        self.divider1.grid(row=0, column=1, sticky="ns")

        self.right_frame = tk.Frame(self.root)
        self.right_frame.grid(row=0, column=2, sticky="nsew")
        self.right_frame.grid_propagate(False)
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)
        # endregion -|1|-

        # region ----|1|---- Left Grid
        self.midia_label = tk.Label(self.left_frame, bg="black")
        self.midia_label.pack(expand=True, fill="both")
        # endregion -|1|-

        # region ----|1|---- Right Grid
        self.filter_frame = tk.Frame(self.right_frame, bg="lightgray", width=self.FILTER_COLUMN_WIDTH)
        self.filter_frame.grid(row=0, column=0, sticky="nsew")
        self.filter_frame.grid_propagate(False)
        # endregion -|1|-

        # region ----|1|---- Select File
        self.file_btn = tk.Button(
            self.filter_frame,
            text="Selecionar arquivo",
            command=self.select_file,
        )

        self.file_btn.pack(fill="x", padx=PADX, pady=PADY)
        # endregion -|1|-

        # region ----|1|---- Select Filter
        self.option_var = tk.StringVar(value="Select Filter")

        self.option_combo = ttk.Combobox(
            self.filter_frame,
            textvariable=self.option_var,
            state="readonly"
        )

        self.option_combo.bind("<<ComboboxSelected>>", self.select_filter)
        # endregion -|1|-

        # region ----|1|---- Filter Params
        self.params_frame = tk.Frame(self.filter_frame, bg="lightgray")
        # endregion -|1|-

    def clear_filter_controls(self) -> None:
        for widget in self.params_frame.winfo_children():
            widget.destroy()

    def add_save_button(self) -> None:
        save_cmd = self.midia.save_video if self.midia.playing else self.midia.save_image
        save_btn = tk.Button(
            self.params_frame,
            text="Save",
            command=lambda: save_cmd(self.filters)
        )
        save_btn.pack(anchor="s")

    def on_close(self):
        self.midia.stop_video_pipeline()
        self.root.destroy()

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Selecione um vídeo",
            filetypes=[
                ("Imagens e vídeos", "*.png *.jpg *.jpeg *.mp4 *.avi"),
                ("Vídeos", "*.mp4 *.avi *.mov *.mkv"),
                ("Imagens", "*.png *.jpg *.jpeg")
            ]
        )

        if not file_path:
            return

        # Set Midia variables
        self.midia.path = file_path
        self.midia.file_ext = os.path.splitext(file_path)[1].lower()

        self.clear_filter_controls()

        # Show filters combobox (sorted alphabetically)
        available_filters = (
            sorted(self.filters.all_filters_map)
            if self.midia.file_ext in VIDEO_EXTENSIONS
            else sorted(self.filters.filters_map)
        )
        self.option_combo["values"] = available_filters

        self.option_combo.pack(padx=PADX, pady=PADY)
        self.params_frame.pack(fill="x", padx=PADX, pady=PADY)

        if self.midia.file_ext in IMAGE_EXTENSIONS:
            self.midia.playing = False
            self.midia.last_render_frame = None

            if self.midia.cap:
                self.midia.stop_video_pipeline()
                self.midia.cap.release()
                self.midia.cap = None

            self.midia.image_layers = [] # Reset
            img = cv2.imread(file_path)
            if img is None:
                messagebox.showerror("Erro", "Nao foi possivel abrir a imagem.")
                return
            self.midia.image_layers.append((0, img))

        elif self.midia.file_ext in VIDEO_EXTENSIONS:
            self.midia.playing = True
            self.midia.image_layers = []

            if self.midia.cap:
                self.midia.stop_video_pipeline()
                self.midia.cap.release()

            self.midia.cap = cv2.VideoCapture(file_path)
            self.midia.fps = self.midia.cap.get(cv2.CAP_PROP_FPS)
            self.frame_counter = 0
            self.next_frame_time = time.perf_counter()
            self.midia.start_video_pipeline(self.filters)

        selected_filter = self.option_var.get()
        if selected_filter in available_filters:
            self.filters.selected = [selected_filter]
            self.build_filter_controls(self.filters.all_filters_map[selected_filter])
            self.midia.update_filter(selected_filter, self.filters.params.get(selected_filter, {}))
            self.add_save_button()
        else:
            self.option_var.set("Select Filter")
            self.filters.selected = []
            self.midia.update_filter("original", {})

        if self.midia.playing:
            self.update_video()
        else:
            self.update_image()

        return file_path if file_path else None

    def prepare_tk_img(self, cv_img: MatLike):
        """
        Resizes cv image to fit UI and turns it into tk image to show.

        :param self:
        :type self: GUI
        :param cv_img:
        :type cv_img: MatLike
        """
        rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)

        h, w = cv_img.shape[:2]
        frame_w = self.left_frame.winfo_width()
        frame_h = self.left_frame.winfo_height()
        scale = min(frame_w / w, frame_h / h)

        new_w = int(scale * w)
        new_h = int(scale * h)

        if new_w == w and new_h == h:
            img_resized = rgb_img
        else:
            img_resized = cv2.resize(rgb_img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        pil_img = Image.fromarray(img_resized)
        tk_img = ImageTk.PhotoImage(pil_img)

        return tk_img

    def update_image(self):
        if not self.midia.image_layers:
            return

        cv_img: MatLike = self.midia.image_layers[0][1]
        if self.filters.selected:
            filt = self.filters.selected[0]
            cv_img = self.filters.apply_filter(cv_img, filt)
        tk_img = self.prepare_tk_img(cv_img)

        self.midia_label.image = tk_img
        self.midia_label.configure(image=tk_img)

    def update_video(self) -> None:
        if not self.midia.playing:
            return
        now = time.perf_counter()

        frame_w = self.left_frame.winfo_width()
        frame_h = self.left_frame.winfo_height()
        if frame_w > 1 and frame_h > 1:
            self.midia.update_preview_max(frame_w, frame_h)

        ui_frame_time = max(self.midia.frame_time, 1.0 / 30.0)

        # Wait to Frame Time
        if now < self.next_frame_time:
            delay_ms = int((self.next_frame_time - now) * 1000)
            self.root.after(max(1, delay_ms), self.update_video)
            return

        if self.midia.render_queue:
            while True:
                try:
                    frame = self.midia.render_queue.get_nowait()
                    self.midia.last_render_frame = frame
                except queue.Empty:
                    break

        if self.midia.last_render_frame is not None:
            tk_frame = self.prepare_tk_img(self.midia.last_render_frame)
            self.midia_label.image = tk_frame
            self.midia_label.configure(image=tk_frame)

        # Prepare next Frame
        self.next_frame_time = now + ui_frame_time
        self.root.after(1, self.update_video)

    def select_filter(self, event: tk.Event) -> None:
        filt = self.option_var.get()
        self.filters.selected = [filt]
        func = self.filters.all_filters_map[filt]

        self.build_filter_controls(func)

        # Update current filter and clear queues for immediate effect
        self.midia.update_filter(filt, self.filters.params.get(filt, {}))

        # Pack Save Button
        self.add_save_button()

        if self.midia.playing:
            self.update_video()
        else:
            self.update_image()
        self.params_frame.pack(fill="both")

    def build_filter_controls(self, filter_fn: Callable):
        self.clear_filter_controls()

        filter_name = filter_fn.__name__
        filter_params: Dict[str, int] = self.filters.params.get(filter_name, {})

        for param, value in filter_params.items():

            label = tk.Label(self.params_frame, text=param)
            label.pack()

            param_controls_grid = tk.Frame(self.params_frame)
            param_controls_grid.grid_rowconfigure(0, weight=1)
            param_controls_grid.grid_columnconfigure(0, weight=1)
            param_controls_grid.grid_columnconfigure(1, weight=1)
            param_controls_grid.grid_columnconfigure(2, weight=1)

            # (Return)
            validate_int_entry = self.root.register(
                lambda s: s in ("", "-") or s.lstrip("-").isdigit()
            )
            param_entry = tk.Entry(
                param_controls_grid,
                width=5,
                textvariable=tk.IntVar(value=value),
                justify="center",
                validate="key",
                validatecommand=(validate_int_entry, "%P")
            )
            param_entry.bind("<Return>",
                             lambda event,f=filter_name, p=param, e=param_entry:
                             self.mod_filter_param(filter_name=f, param=p, entry=e))
            param_entry.grid(row=0, column=1)

            # (-)
            minus_btn = tk.Button(
                param_controls_grid,
                text="-",
                command=(
                    lambda f=filter_name, e=param_entry, p=param:
                        self.mod_filter_param(filter_name=f, param=p, signal="-", entry=e)
                )
            )
            minus_btn.grid(row=0, column=0, sticky="ew")

            # (+)
            plus_btn = tk.Button(
                param_controls_grid,
                text="+",
                command=(
                    lambda f=filter_name, e=param_entry, p=param:
                        self.mod_filter_param(filter_name=f, param=p, signal="+", entry=e)
                )
            )
            plus_btn.grid(row=0, column=2, sticky="ew")

            # Pack
            param_controls_grid.pack(padx=30, pady=PADY)

    def mod_filter_param(self, filter_name: str, param: str, signal: str|None=None, entry: tk.Entry|None=None) -> None:
        if signal == "-":
            value = self.filters.params[filter_name][param] - 1

        elif signal == "+":
            value = self.filters.params[filter_name][param] + 1

        else:
            value = int(entry.get())

        int_var = tk.IntVar(name=entry["textvariable"])

        frame_ref = None
        if self.midia.playing:
            with self.midia.filter_lock:
                frame_ref = self.midia.last_frame
        else:
            frame_ref = self.midia.image_layers[-1][1] if self.midia.image_layers else None

        self.filters.set_param(filter_name, param, value, frame_ref)
        new_value = self.filters.params[filter_name][param]
        int_var.set(new_value)

        # Update filter params in pipeline and clear queues
        if self.midia.playing:
            self.midia.update_filter(filter_name, self.filters.params.get(filter_name, {}))

        if not self.midia.playing:
            self.update_image()


def main():

    filters = Filters()

    midia = Midia()

    gui = GUI(filters, midia)

    gui.root.mainloop()


if __name__ == "__main__":
    main()
