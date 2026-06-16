# Gesture Control — Beta v0.1

App de escritorio que controla el **brillo** y el **volumen** del sistema
usando gestos de mano frente a tu cámara.

---

## Cómo obtener los 3 instaladores (macOS · Windows · Linux)

Los instaladores se generan automáticamente en la nube con GitHub Actions.
Solo necesitas hacer esto **una vez**:

### Paso 1 — Sube el proyecto a GitHub

```bash
git init
git add .
git commit -m "v1.0.0"

# Crea un repo en github.com y luego:
git remote add origin https://github.com/TU_USUARIO/gesture-control.git
git push -u origin main
```

### Paso 2 — Crea un tag para lanzar la compilación

```bash
git tag v1.0.0
git push origin v1.0.0
```

Esto activa GitHub Actions automáticamente. En ~10 minutos tendrás los 3 instaladores listos.

### Paso 3 — Descarga los instaladores

Ve a tu repositorio en GitHub → **Releases** → `v1.0.0`

Ahí encontrarás:
- `GestureControl-mac.dmg` — macOS (ventana drag-to-Applications)
- `GestureControl-Setup.exe` — Windows (crea acceso directo en escritorio)
- `GestureControl.AppImage` — Linux (ejecutable directo)

Descárgalos y súbelos a tu página web.

---

## Cómo usar la app

| Mano | Zona de la cámara | Controla |
|------|-------------------|----------|
| Una mano | Lado **izquierdo** | 🔊 Volumen |
| Una mano | Lado **derecho** | ☀️ Brillo |
| Ambas manos | Izquierda + Derecha | Los dos a la vez |

**Gesto:** Pellizca (junta el pulgar y el índice).
Más cerrado = menos · Más abierto = más.

---

## Estructura del proyecto

```
gesture-control/
├── .github/
│   └── workflows/
│       └── build.yml          ← GitHub Actions: compila los 3 instaladores
├── main.py                    ← Interfaz, cámara y lógica de gestos
├── system_control.py          ← Control de brillo y volumen por OS
├── gesture_control.spec       ← Configuración de PyInstaller
├── requirements.txt           ← Dependencias Python
└── README.md
```
