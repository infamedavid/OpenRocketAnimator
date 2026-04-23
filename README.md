# 🚀 OpenRocket Animador (ORA) - Addon para Blender


![Logo](https://github.com/infamedavid/OpenRocketAnimator/blob/main/ORA_icon.png)

**ORA** es un addon para [Blender](https://www.blender.org) que permite importar modelos 3D exportados desde [OpenRocket](https://openrocket.info/) y animarlos usando datos de simulación en formato CSV. Ideal para crear visualizaciones de vuelos de cohetes en 3D con precisión física.

---

## 🛠️ Características

### 1. **Importa un Modelo de Cohete**
- Carga un archivo `.obj` (exportado desde OpenRocket).
- Incluye una opción para corregir la escala del modelo.

### 2. **Carga Datos de la Simulación de Vuelo**
- Carga un archivo `.csv` generado por OpenRocket.
- Detecta automáticamente las columnas necesarias (posición, tiempo, rotación).

### 3. **Anima con los Datos de La Simulacion**
- Anima la posición y opcionalmente el **roll** del cohete.
- Puedes especificar:
  - **Offset de inicio (frames)**.
  - **Frecuencia de keyframes** (útil para controlar el número de cuadros insertados).
  - **Activar o desactivar rotación (roll)**.

### 4. **Maneja las Camaras y pone en Foco tu Cohete**
- Haz que la camara activa apunte directamente al cohete y lo siga en su trayectoria.
- Puedes anadir nuevas camaras  montadas sobre el cohete y hacer que se sacudan para mayor dramatismo
  
---

## 📦 Instalación

1. Descarga el archivo [`ORA2.zip`](https://github.com/infamedavid/OpenRocketAnimator/tree/main/assets).
2. ejecuta Blender.
3. Dirigete a Edit/Preferences/Add-ons.
4. En la esquina superior derecha selecciona"Install from File " navega hasta la carpeta  donde descargate el zip seleccionalo  y listo!`.

---

## ✅ Modo de Uso

1. **Importa el modelo OBJ**
   - Exporta desde OpenRocket en formato OBJ.
   - En Blender, usa el panel *OpenRocket* en la barra lateral (`N`).
   - Selecciona el archivo OBJ y presiona **"Importar OBJ"**.
   - Si el modelo se ve demasiado grande/pequeño, ajusta el factor de escala y usa **"Corregir Escala"**.

2. **Cargar Simulación**
   - Selecciona el archivo CSV con los datos de simulación.

3. **Configura la animación**
   - Define si deseas incluir **rotación (roll)**.
   - Ajusta el **offset de inicio** y la **frecuencia de keyframes**.

4. **Generar animación**
   - Haz clic en **"Animar desde CSV"**.

5. *(Opcional)* Usa el botón **"Animación Lineal"** para hacer que las curvas tengan interpolación lineal, evitando aceleración/desaceleración automática que produce el modo Bézier cuando la frecuencia de keyframes es diferente a 1. esto es útil para mantener una simulación técnica más precisa.

---

## 🧪 Requisitos

- Blender 4.0 o superior.
- Modelo `.obj` y simulación `.csv` exportados desde [OpenRocket](https://openrocket.info/).

---

## ✅ Manual test checklist (Rocket Camera)

- Change **Y Offset (m)** and confirm the mounted rocket camera moves immediately in local Y.
- Change **Z Rotation** and confirm the mounted rocket camera rotates immediately around local Z.
- Confirm these live edits use delta transforms and do not overwrite the base mount transform.
- Press **Update Camera** and confirm the base mount is rebuilt while live offsets remain applied.

---

## 📜 Licencia

Este addon se distribuye bajo la licencia **GPL-3.0**.

**SIN GARANTÍA**: El autor no se hace responsable del uso que se le dé al addon ni de los resultados obtenidos.

---


