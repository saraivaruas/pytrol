## Qué cambia y por qué

<!-- Describe el problema y la solución en pocas líneas. Enlaza el issue: Closes #123 -->

## Cómo se probó

- [ ] `python3 -m unittest discover -s tests` pasa (necesita una pantalla; en un servidor: `xvfb-run -a …`)
- [ ] Agregué o actualicé pruebas para el cambio
- [ ] Probé en: <!-- distribución, X11 o Wayland, y cómo lo instalaste -->

## Lista de verificación

- [ ] No agrega dependencias: solo Python 3, PyGObject, GTK 3, VTE y GtkSourceView 4
- [ ] Los textos para el usuario están en español
- [ ] Respeta la sesión del usuario: no borra ni sobrescribe sin avisar lo guardado
- [ ] Si cambia algo visible, actualicé el README, el CHANGELOG y las capturas (`tools/capturar-pantallas.py`)
