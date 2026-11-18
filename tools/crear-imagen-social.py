#!/usr/bin/env python3
"""Crea las imágenes de presentación de Pytrol.

- docs/social-preview.png (1280x640): la que GitHub muestra al compartir el repositorio.
  Subir a mano: GitHub → Settings → General → Social preview.
- packaging/store/banner.png (1920x640, 3:1) e icon.png (512x512): para la ficha de la Snap Store.

Mismo estilo que la de Sentinel: fondo oscuro con un resplandor, icono, nombre, descripción y etiquetas.
Requiere Pillow y ImageMagick (convert, para pasar el icono SVG a PNG).
"""
import subprocess
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

AQUI = Path(__file__).resolve().parent.parent
ICONO = AQUI / "data/icons/io.github.saraivaruas.Pytrol.svg"
TIENDA = AQUI / "packaging/store"
FUENTES = "/usr/share/fonts/truetype/dejavu/"


def fuente(negrita, tam):
    return ImageFont.truetype(FUENTES + ("DejaVuSans-Bold.ttf" if negrita else "DejaVuSans.ttf"), tam)


def componer(W, H, salida):
    img = Image.new("RGB", (W, H), "#0a0f1e")
    # Resplandor violeta arriba a la derecha: elipse difuminada usada como máscara.
    mascara = Image.new("L", (1400, 1100), 0)
    ImageDraw.Draw(mascara).ellipse((350, 250, 1050, 850), fill=150)
    mascara = mascara.filter(ImageFilter.GaussianBlur(150))
    img.paste(Image.new("RGB", (1400, 1100), "#5046c8"), (W - 1050, -650), mascara)
    d = ImageDraw.Draw(img)

    icono = subprocess.run(["convert", "-background", "none", "-density", "600", str(ICONO), "-resize", "96x96", "png:-"],
                           check=True, capture_output=True).stdout
    icono = Image.open(BytesIO(icono)).convert("RGBA")
    img.paste(icono, (90, 150), icono)
    d.text((212, 138), "Pytrol", font=fuente(True, 86), fill="#eef2ff")
    d.text((90, 272), "Terminal avanzado para Linux", font=fuente(True, 34), fill="#cdd6f6")
    d.text((90, 338), "Paneles divisibles · proyectos por panel · árbol de archivos", font=fuente(False, 24), fill="#8f9bbd")
    d.text((90, 378), "editor integrado · sesión persistente · atajos configurables", font=fuente(False, 24), fill="#8f9bbd")

    x = 90
    for texto in ("MIT", "Python + GTK 3 + VTE", "Open source"):
        f = fuente(True, 22)
        ancho = d.textlength(texto, font=f) + 36
        d.rounded_rectangle((x, 450, x + ancho, 492), radius=10, fill="#161e36", outline="#2e3a6b", width=1)
        d.text((x + 18, 458), texto, font=f, fill="#eef2ff")
        x += ancho + 14
    img.save(salida, optimize=True)
    print(f"  {salida.relative_to(AQUI)}")


def main():
    componer(1280, 640, AQUI / "docs/social-preview.png")
    TIENDA.mkdir(parents=True, exist_ok=True)
    componer(1920, 640, TIENDA / "banner.png")
    subprocess.run(["convert", "-background", "none", "-density", "800", str(ICONO), "-resize", "512x512", "-depth", "8",
                    str(TIENDA / "icon.png")], check=True)
    print(f"  {(TIENDA / 'icon.png').relative_to(AQUI)}")


if __name__ == "__main__":
    main()
