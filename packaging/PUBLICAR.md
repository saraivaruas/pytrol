# Publicar Pytrol (lo que hace cada tienda y qué haces tú)

Lo técnico está listo y se prueba solo en cada cambio (`.github/workflows/`). Lo que sigue necesita **tus cuentas**; yo no las creo ni las uso, y nada de esto sube nada por su cuenta.

## 0. GitHub (una vez)

1. Con la CLI `gh` autenticada: `tools/configurar-github.sh` (descripción, temas, reportes privados de seguridad). Con `PROTEGER_MAIN=1` además deja `main` protegida: después, todo cambio entra por Pull Request, también los de «Manifest de envío a Flathub».
2. Sube a mano la imagen social: Settings → General → **Social preview** → `docs/social-preview.png` (GitHub no tiene API para esto).
3. `git push` cuando quieras publicar. Las capturas del README y del metainfo se ven desde `main`.
4. Si cambias algo visible, regenera las capturas antes: `tools/capturar-pantallas.py`.

## 1. Flathub (gratis)

Ya está preparado en `flathub/` (manifest con la etiqueta de cada versión). El paso a paso está en el README, sección «Publicar en Flathub». Cada versión nueva: etiqueta `vX.Y.Z`, commit del manifest con esa etiqueta y PR a `flathub/<app-id>`.

## 2. Snap Store

Dos paquetes, en este orden. Los construye `./scripts/construir-snap.sh` o la CI (artefactos del trabajo `snap` y `snap-beta`).

**a) Beta (devmode), sin esperar a nadie**
1. Cuenta en https://snapcraft.io y `snapcraft login`.
2. `snapcraft register pytrol` (si el nombre está tomado, cambia `name:` en `snap/snapcraft.yaml`).
3. `snapcraft upload --release=beta pytrol_X.Y.Z-beta_amd64.snap`. Un snap devmode solo puede ir a `beta` y `edge`. **Hecho el 17-11-2026: revisión 1 (0.6.4-beta) en `beta`.**
4. Límites: el shell de los paneles corre sobre el sistema de archivos de core22, sin tu `git` ni tus herramientas; sirve para probar la ventana, los paneles y el editor.

**Ficha con imágenes (hecho el 17-11-2026):** `snapcraft upload-metadata <archivo.snap>` envía resumen, descripción e icono. El banner y las capturas se suben a mano en https://snapcraft.io/pytrol/listing; los archivos y el orden están en [packaging/store/README.md](store/README.md).

**b) Classic (el definitivo)**
1. La revisión classic ya está subida (`snapcraft upload pytrol_X.Y.Z_amd64.snap`, sin `--release`); la Store la deja «pendiente de revisión manual».
2. **Hecho el 17-11-2026:** tema https://forum.snapcraft.io/t/classic-confinement-request-for-pytrol/54260. (Si hubiera que repetirlo, crea un tema en https://forum.snapcraft.io/c/store-requests/classic-confinement/26 (categoría `classic-confinement`) con el texto de [packaging/store/solicitud-classic.md](store/solicitud-classic.md). Un revisor humano lo aprueba.)
3. Con la aprobación: `snapcraft release pytrol <revisión> candidate`, y cuando lo pruebes, `stable`.

## 3. Lista antes de cada versión

- [ ] `CHANGELOG.md`, `data/…metainfo.xml` (nuevo `<release>`) y `README.md` al día.
- [ ] Capturas regeneradas si cambió algo visible.
- [ ] Etiqueta `vX.Y.Z`; commit «Manifest de envío a Flathub: etiqueta vX.Y.Z».
- [ ] Snap beta y classic construidos desde esa misma etiqueta y subidos.
