import json
import os
import re
from datetime import datetime
from kivy.app import App
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

try:
  from PIL import Image as PILImage, ImageOps

  PIL_AVAILABLE = True
except ImportError:
  PIL_AVAILABLE = False

try:
  from jnius import autoclass, cast

  ANDROID = True
except ImportError:
  ANDROID = False


MAX_CARPETAS = 100


def limpiar_nombre(texto):
  """Quita caracteres que no sirven en nombres de carpeta/archivo."""
  return re.sub(r'[\\/:*?"<>|]+', "_", texto).strip()


def etiqueta(texto, **kwargs):
  """Label que ajusta el texto a su tamaño y lo centra."""
  lbl = Label(text=texto, halign="center", valign="middle", **kwargs)
  lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
  return lbl


class CardLayout(BoxLayout):

  def __init__(self, bg_color=(0.15, 0.18, 0.22, 1), **kwargs):
    super(CardLayout, self).__init__(**kwargs)
    with self.canvas.before:
      Color(*bg_color)
      self.rect = RoundedRectangle(
          pos=self.pos, size=self.size, radius=[15]
      )
    self.bind(pos=self.update_rect, size=self.update_rect)

  def update_rect(self, *args):
    self.rect.pos = self.pos
    self.rect.size = self.size


class RoundedButton(Button):

  def __init__(self, bg_color=(0.1, 0.65, 0.3, 1), radius=[35], **kwargs):
    super(RoundedButton, self).__init__(**kwargs)
    self.bg_color = bg_color
    self.radius = radius
    self.background_normal = ""
    self.background_down = ""
    self.background_color = (0, 0, 0, 0)

    with self.canvas.before:
      self.inst_color = Color(*self.bg_color)
      self.rect = RoundedRectangle(
          pos=self.pos, size=self.size, radius=self.radius
      )
    self.bind(pos=self.update_rect, size=self.update_rect)

  def update_rect(self, *args):
    self.rect.pos = self.pos
    self.rect.size = self.size

  def set_bg_color(self, color):
    self.bg_color = color
    self.inst_color.rgba = color


class CustomCameraApp(App):

  def build(self):
    from kivy.core.window import Window

    Window.clearcolor = (0.08, 0.10, 0.12, 1)

    estado = self.load_state()
    self.base_dir = estado["base_dir"]
    saved_lote = estado["lote"]
    saved_modelo = estado["modelo"]
    saved_ancho = estado["ancho"]
    saved_alto = estado["alto"]
    saved_calidad = estado["calidad"]
    try:
      self.sub_indice = max(0, int(estado["subindice"]))
    except ValueError:
      self.sub_indice = 0

    root_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)

    self.layout = BoxLayout(
        orientation="vertical", padding=25, spacing=20, size_hint_y=None
    )
    self.layout.bind(minimum_height=self.layout.setter("height"))

    # --- 1 y 2. LOTE Y MODELO EN UNA SOLA LÍNEA ---
    lote_modelo_card = CardLayout(
        orientation="horizontal",
        padding=15,
        spacing=15,
        size_hint_y=None,
        height=210,
        bg_color=(0.14, 0.18, 0.24, 1),
    )

    # LOTE (Excepción: tamaño de fuente más grande)
    col_lote = BoxLayout(orientation="vertical", spacing=5, size_hint_x=0.65)
    col_lote.add_widget(
        Label(
            text="LOTE:",
            font_size=40,
            size_hint_y=None,
            height=50,
            color=(0.7, 0.8, 1, 1),
        )
    )
    self.lote_input = TextInput(
        text=saved_lote,
        font_size=75,
        multiline=False,
        size_hint_y=None,
        height=100,
        halign="center",
        background_color=(0.2, 0.24, 0.3, 1),
        foreground_color=(1, 1, 1, 1),
    )
    self.lote_input.bind(
        text=lambda instance, value: (self.save_state(), self.actualizar_conteo())
    )
    col_lote.add_widget(self.lote_input)
    lote_modelo_card.add_widget(col_lote)

    # MODELO (Limitado a 7 caracteres, fuente grande y centrada)
    col_modelo = BoxLayout(orientation="vertical", spacing=5, size_hint_x=0.35)
    col_modelo.add_widget(
        Label(
            text="MODELO:",
            font_size=40,
            size_hint_y=None,
            height=50,
            color=(1, 0.82, 0, 1),
        )
    )
    self.modelo_input = TextInput(
        text=saved_modelo[:7],
        font_size=65,
        multiline=False,
        size_hint_y=None,
        height=100,
        halign="center",
        background_color=(0.2, 0.24, 0.3, 1),
        foreground_color=(1, 1, 1, 1),
    )

    def limitar_modelo(instance, value):
      if len(value) > 7:
        instance.text = value[:7]
      self.save_state()
      self.actualizar_conteo()

    self.modelo_input.bind(text=limitar_modelo)
    col_modelo.add_widget(self.modelo_input)
    lote_modelo_card.add_widget(col_modelo)

    self.layout.add_widget(lote_modelo_card)

    # --- 3, 4 y 5. ANCHO, ALTO Y CALIDAD EN UNA SOLA LÍNEA ---
    params_card = CardLayout(
        orientation="horizontal",
        padding=15,
        spacing=15,
        size_hint_y=None,
        height=210,
        bg_color=(0.14, 0.18, 0.24, 1),
    )

    # ANCHO
    col_ancho = BoxLayout(orientation="vertical", spacing=5)
    col_ancho.add_widget(
        Label(
            text="ANCHO",
            font_size=40,
            size_hint_y=None,
            height=50,
            color=(0.8, 0.8, 1, 1),
        )
    )
    self.ancho_input = TextInput(
        text=saved_ancho,
        font_size=65,
        multiline=False,
        input_filter="int",
        size_hint_y=None,
        height=100,
        halign="center",
        background_color=(0.2, 0.24, 0.3, 1),
        foreground_color=(1, 1, 1, 1),
    )
    self.ancho_input.bind(text=lambda instance, value: self.save_state())
    col_ancho.add_widget(self.ancho_input)
    params_card.add_widget(col_ancho)

    # ALTO
    col_alto = BoxLayout(orientation="vertical", spacing=5)
    col_alto.add_widget(
        Label(
            text="ALTO",
            font_size=40,
            size_hint_y=None,
            height=50,
            color=(0.8, 0.8, 1, 1),
        )
    )
    self.alto_input = TextInput(
        text=saved_alto,
        font_size=65,
        multiline=False,
        input_filter="int",
        size_hint_y=None,
        height=100,
        halign="center",
        background_color=(0.2, 0.24, 0.3, 1),
        foreground_color=(1, 1, 1, 1),
    )
    self.alto_input.bind(text=lambda instance, value: self.save_state())
    col_alto.add_widget(self.alto_input)
    params_card.add_widget(col_alto)

    # CALIDAD
    col_calidad = BoxLayout(orientation="vertical", spacing=5)
    col_calidad.add_widget(
        Label(
            text="CALIDAD",
            font_size=40,
            size_hint_y=None,
            height=50,
            color=(0.6, 0.9, 0.6, 1),
        )
    )
    self.calidad_input = TextInput(
        text=saved_calidad,
        font_size=65,
        multiline=False,
        input_filter="int",
        size_hint_y=None,
        height=100,
        halign="center",
        background_color=(0.2, 0.24, 0.3, 1),
        foreground_color=(1, 1, 1, 1),
    )
    self.calidad_input.bind(text=lambda instance, value: self.save_state())
    col_calidad.add_widget(self.calidad_input)
    params_card.add_widget(col_calidad)

    self.layout.add_widget(params_card)

    # --- TARJETA PRINCIPAL DE CARPETAS Y FOTOS (CON LETRAS MÁS GRANDES) ---
    sub_card = CardLayout(
        orientation="vertical",
        padding=15,
        spacing=12,
        size_hint_y=None,
        height=580,
        bg_color=(0.14, 0.18, 0.24, 1),
    )

    # 1. ETIQUETA DE CONTEO DE FOTOS (MUY GRANDE ARRIBA)
    self.count_label = etiqueta(
        "FOTOS EN ESTA CARPETA: 0",
        font_size=52,
        bold=True,
        size_hint_y=None,
        height=100,
        color=(0.9, 0.9, 1, 1),
    )
    sub_card.add_widget(self.count_label)

    # 2. ETIQUETA EN GRANDE ("Carpeta XX" - MUY GRANDE)
    self.sub_label = etiqueta(
        "",
        font_size=75,
        bold=True,
        size_hint_y=None,
        height=130,
        color=(0.6, 0.9, 0.6, 1),
    )
    sub_card.add_widget(self.sub_label)

    # 3. TÍTULO DE SUBCARPETAS
    sub_card.add_widget(
        etiqueta(
            "SUBCARPETAS:",
            font_size=35,
            size_hint_y=None,
            height=50,
            color=(1, 0.82, 0, 1),
        )
    )

    # 4. BOTONES Y CANTIDAD DE SUBCARPETAS (ABAJO)
    fila_nav = BoxLayout(
        orientation="horizontal", spacing=15, size_hint_y=None, height=140
    )
    btn_atras = RoundedButton(
        text="<",
        font_size=80,
        bold=True,
        bg_color=(0.4, 0.4, 0.45, 1),
        radius=[25],
        size_hint_x=0.32,
    )
    btn_atras.bind(on_press=self.sub_atras)

    self.subcant_input = TextInput(
        text=estado["subcant"],
        font_size=90,
        multiline=False,
        input_filter="int",
        halign="center",
        size_hint_x=0.36,
        background_normal="",
        background_active="",
        background_color=(0, 0, 0, 0),
        foreground_color=(1, 1, 1, 1),
        cursor_color=(1, 1, 1, 1),
    )
    self.subcant_input.bind(text=self.on_subcant_cambiada)

    btn_adelante = RoundedButton(
        text=">",
        font_size=80,
        bold=True,
        bg_color=(0.1, 0.45, 0.75, 1),
        radius=[25],
        size_hint_x=0.32,
    )
    btn_adelante.bind(on_press=self.sub_adelante)

    fila_nav.add_widget(btn_atras)
    fila_nav.add_widget(self.subcant_input)
    fila_nav.add_widget(btn_adelante)
    sub_card.add_widget(fila_nav)

    self.layout.add_widget(sub_card)

    # --- 7. BOTÓN DE TOMAR FOTO ---
    self.btn_open_cam = RoundedButton(
        text="TOMAR FOTO",
        font_size=70,
        bold=True,
        bg_color=(0.1, 0.65, 0.3, 1),
        radius=[30],
        size_hint_y=None,
        height=140,
    )
    self.btn_open_cam.bind(on_press=self.open_native_camera)
    self.layout.add_widget(self.btn_open_cam)

    # --- 8. MENSAJES DE ESTADO ---
    self.status_label = etiqueta(
        "",
        font_size=34,
        size_hint_y=None,
        height=90,
        color=(0.7, 0.9, 0.7, 1),
    )
    self.layout.add_widget(self.status_label)

    root_scroll.add_widget(self.layout)

    self.sub_indice = min(self.sub_indice, self.cantidad_subcarpetas())
    self._ui_listo = True
    self.actualizar_conteo()

    return root_scroll

  # ------------------------------------------------------------------
  # Estado guardado
  # ------------------------------------------------------------------
  def get_state_file_path(self):
    return os.path.join(self.user_data_dir, "app_state.json")

  def default_base_dir(self):
    if ANDROID:
      try:
        Environment = autoclass("android.os.Environment")
        dcim = Environment.getExternalStoragePublicDirectory(
            Environment.DIRECTORY_DCIM
        ).getAbsolutePath()
        return os.path.join(dcim, "PYTHON")
      except Exception:
        pass
    return os.path.join(os.path.expanduser("~"), "PYTHON")

  def load_state(self):
    estado = {
        "lote": "LOTE01",
        "modelo": "MOD_A",
        "ancho": "1280",
        "alto": "720",
        "calidad": "90",
        "base_dir": self.default_base_dir(),
        "subcant": "5",
        "subindice": "0",
    }
    path = self.get_state_file_path()
    if os.path.exists(path):
      try:
        with open(path, "r") as f:
          data = json.load(f)
        if isinstance(data, dict):
          estado.update({k: v for k, v in data.items() if k in estado})
      except Exception:
        pass
    return estado

  def save_state(self):
    if not getattr(self, "_ui_listo", False):
      return
    path = self.get_state_file_path()
    try:
      data = {
          "lote": self.lote_input.text.strip().upper(),
          "modelo": self.modelo_input.text.strip().upper()[:7],
          "ancho": self.ancho_input.text.strip(),
          "alto": self.alto_input.text.strip(),
          "calidad": self.calidad_input.text.strip(),
          "base_dir": self.base_dir,
          "subcant": self.subcant_input.text.strip(),
          "subindice": str(self.sub_indice),
      }
      with open(path, "w") as f:
        json.dump(data, f)
    except Exception as e:
      print(f"Error guardando JSON: {e}")

  # ------------------------------------------------------------------
  # Carpetas y ubicación
  # ------------------------------------------------------------------
  def mostrar_estado(self, texto, error=False):
    self.status_label.color = (1, 0.5, 0.5, 1) if error else (0.7, 0.9, 0.7, 1)
    self.status_label.text = texto

  def carpeta_base(self):
    """Carpeta del lote, sin la subcarpeta."""
    lote = limpiar_nombre(self.lote_input.text.strip().upper()) or "SIN_LOTE"
    return os.path.join(self.base_dir, lote)

  def cantidad_subcarpetas(self):
    try:
      return max(
          0, min(int(self.subcant_input.text.strip() or 0), MAX_CARPETAS)
      )
    except ValueError:
      return 0

  def carpeta_modelo(self):
    """Nombre de la carpeta del modelo (máx. 7 caracteres)."""
    return (
        limpiar_nombre(self.modelo_input.text.strip().upper()[:7])
        or "SIN_MODELO"
    )

  def obtener_carpeta_destino(self):
    """Ruta completa donde se guardará la próxima foto.

    - Carpeta 00: LOTE/00 (fotos generales, sin relación con modelos).
    - Carpetas 01, 02, ...: LOTE/MODELO/01, LOTE/MODELO/02, ...
    """
    if self.sub_indice == 0:
      return os.path.join(self.carpeta_base(), "00")
    return os.path.join(
        self.carpeta_base(), self.carpeta_modelo(), f"{self.sub_indice:02d}"
    )

  def on_subcant_cambiada(self, instance, value):
    cant = self.cantidad_subcarpetas()
    if self.sub_indice > cant:
      self.sub_indice = cant
    self.save_state()
    self.actualizar_conteo()

  def sub_atras(self, instance):
    if self.sub_indice > 0:
      self.sub_indice -= 1
      self.save_state()
      self.actualizar_conteo()

  def sub_adelante(self, instance):
    if self.sub_indice < self.cantidad_subcarpetas():
      self.sub_indice += 1
      self.save_state()
      self.actualizar_conteo()

  def actualizar_label_subcarpeta(self):
    if self.sub_indice == 0:
      self.sub_label.text = "Carpeta 00"
    else:
      self.sub_label.text = f"Carpeta {self.sub_indice:02d}"

  # ------------------------------------------------------------------
  # Conteo y cámara
  # ------------------------------------------------------------------
  def actualizar_conteo(self):
    if not getattr(self, "_ui_listo", False):
      return
    self.actualizar_label_subcarpeta()
    try:
      carpeta = self.obtener_carpeta_destino()
      if os.path.isdir(carpeta):
        cantidad = len(
            [f for f in os.listdir(carpeta) if f.lower().endswith(".jpg")]
        )
      else:
        cantidad = 0
    except Exception:
      cantidad = 0
    self.count_label.text = f"FOTOS EN ESTA CARPETA: {cantidad}"

  def open_native_camera(self, instance):
    if not ANDROID:
      return

    lote_text = limpiar_nombre(self.lote_input.text.strip().upper()) or "SIN_LOTE"
    modelo_text = (
        limpiar_nombre(self.modelo_input.text.strip().upper()[:7]) or "FOTO"
    )

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    full_filename = f"{lote_text}_{modelo_text}_{timestamp}"

    try:
      StrictMode = autoclass("android.os.StrictMode")
      builder = autoclass("android.os.StrictMode$VmPolicy$Builder")
      StrictMode.setVmPolicy(builder().build())

      PythonActivity = autoclass("org.kivy.android.PythonActivity")
      Intent = autoclass("android.content.Intent")
      MediaStore = autoclass("android.provider.MediaStore")
      File = autoclass("java.io.File")
      Uri = autoclass("android.net.Uri")

      current_activity = PythonActivity.mActivity

      carpeta_destino = self.obtener_carpeta_destino()
      os.makedirs(carpeta_destino, exist_ok=True)

      self.photo_file = File(carpeta_destino, f"{full_filename}.jpg")

      photo_uri = Uri.parse("file://" + self.photo_file.getAbsolutePath())
      uri_parcelable = cast("android.os.Parcelable", photo_uri)

      intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
      intent.putExtra(MediaStore.EXTRA_OUTPUT, uri_parcelable)

      current_activity.startActivityForResult(intent, 0x123)

      from kivy.clock import Clock

      Clock.schedule_once(
          lambda dt: self.corregir_orientacion_y_redimensionar(), 2.0
      )

    except Exception as e:
      print(f"Error al abrir cámara: {e}")
      self.mostrar_estado(f"No se pudo abrir la cámara: {e}", error=True)

  def corregir_orientacion_y_redimensionar(self):
    if not PIL_AVAILABLE:
      print("Pillow no está disponible.")
      return

    try:
      if hasattr(self, "photo_file") and self.photo_file.exists():
        ruta_path = self.photo_file.getAbsolutePath()

        with PILImage.open(ruta_path) as img:
          img = ImageOps.exif_transpose(img)

          orig_width, orig_height = img.size

          base_ancho = int(self.ancho_input.text.strip() or 1280)
          base_alto = int(self.alto_input.text.strip() or 720)
          calidad_val = int(self.calidad_input.text.strip() or 90)
          calidad_val = max(1, min(100, calidad_val))

          es_vertical_real = orig_height > orig_width
          es_vertical_config = base_alto > base_ancho

          if es_vertical_real != es_vertical_config:
            ancho_deseado = base_alto
            alto_deseado = base_ancho
          else:
            ancho_deseado = base_ancho
            alto_deseado = base_alto

          img_resized = img.resize(
              (ancho_deseado, alto_deseado), PILImage.Resampling.LANCZOS
          )
          img_resized.save(ruta_path, "JPEG", quality=calidad_val)

          self.actualizar_conteo()
          self.mostrar_estado(
              "Foto guardada en: "
              + os.path.relpath(os.path.dirname(ruta_path), self.base_dir)
          )
    except Exception as ex:
      print(f"Error al procesar la foto: {ex}")


if __name__ == "__main__":
  CustomCameraApp().run()
