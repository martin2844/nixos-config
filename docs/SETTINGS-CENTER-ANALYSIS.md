# Ajustes de Plasma y ampliación de HyprMod

Analysis dated 8 September 2026. The initial proposal below has now been
implemented as three English pages in our HyprMod package. See
[implementation and validation](../packages/hyprmod/README.md) for the current
scope, including the optional brightness limitation and unchanged automatic
sleep policy. The original comparison is retained below for context.

Requisito del usuario: por ahora, ningún apagado, suspensión ni hibernación
automáticos. La futura página debe conservar «Nunca» para estas acciones; no
activar temporizadores al instalarla. Bloquear o apagar solo la pantalla es
independiente de suspender el PC. La configuración actual mantiene el bloqueo
a los 10 minutos y el apagado de pantalla a los 15 minutos.

## Conclusión

Es viable ampliar nuestro paquete de HyprMod con páginas nativas de brillo y
energía/suspensión. Replicar todos los módulos de Plasma sería mantener un
centro de control completo. La propuesta es integrar las funciones básicas y
abrir herramientas existentes para las demás, desde una navegación común.

## Inventario aproximado de Plasma

Se consultó `kcmshell6 --list` en este equipo: 106 módulos disponibles, incluyendo
diagnósticos de Info Center, módulos móviles y variantes X11. No son 106 páginas
distintas visibles en System Settings. `systemsettings --version`: 6.6.6.

| Área | Ajustes de Plasma | Equivalente propuesto para Hyprland |
| --- | --- | --- |
| Pantallas | Resolución, frecuencia, escala, disposición, orientación | HyprMod ya ofrece configuración de monitores; validar cada capacidad del compositor |
| Brillo | Brillo de pantalla, atenuación y, según hardware, teclado | Página nueva: DDC/CI para monitor externo; backlight para portátiles |
| Color de pantalla | Luz nocturna, temperatura y gestión de color según versión | Integración específica con herramientas de Hyprland; no reutilizar los ajustes de KWin |
| Energía | Ahorro/equilibrado/rendimiento, batería, consumo, suspensión | Página nueva sobre power-profiles-daemon, UPower, logind e hypridle |
| Bloqueo | Tiempo de bloqueo, apariencia y desbloqueo al volver | hypridle e hyprlock; integración prevista por upstream, aún no incluida |
| Apariencia | Tema global, estilo Plasma, estilo de aplicaciones, colores, iconos, cursor, fuentes, sonidos | HyprMod cubre decoración del compositor y cursor parcialmente; integrar nuestro desktop-theme y herramientas de Qt/GTK |
| Fondo | Fondo de escritorio y pantalla de bienvenida | Reutilizar nuestra gestión de fondos; hyprpaper previsto en HyprMod |
| Ventanas | Foco, acciones, bordes, efectos, reglas, selector de ventanas | HyprMod ya cubre muchas opciones; funciones específicas de KWin necesitan equivalentes |
| Espacios de trabajo | Escritorios virtuales, actividades, bordes y gestos | Workspaces y gestos de Hyprland; Activities no tiene equivalencia directa |
| Atajos | Atajos globales y de aplicaciones | HyprMod para Hyprland; atajos internos siguen en cada aplicación |
| Entrada | Teclado, distribución, ratón, touchpad, tableta, táctil, teclado virtual, mandos | HyprMod para opciones de entrada del compositor; herramientas adicionales para calibración y dispositivos especiales |
| Audio | Salida, micrófono, volumen, perfiles y dispositivos | Abrir el mezclador existente y reutilizar PipeWire |
| Red | Wi-Fi, Ethernet, VPN, proxy, hotspot, red móvil | NetworkManager y herramientas existentes; proxy global requiere definir qué aplicaciones lo respetan |
| Bluetooth | Adaptadores, emparejamiento y dispositivos | Blueman/BlueZ ya disponibles |
| Notificaciones | Avisos por aplicación, sonido, no molestar | SwayNotificationCenter y configuración de cada aplicación; KNotifications no gobierna todo Hyprland |
| Aplicaciones | Predeterminadas, asociaciones de archivo y carpetas personales | MIME/XDG; reutilizar editores compatibles y los archivos enlazados del repo |
| Inicio y sesión | Autostart, servicios de fondo, SDDM, inicio/cierre de sesión | HyprMod para autostart; UWSM/systemd/NixOS para servicios y SDDM |
| Búsqueda | Indexado de archivos, búsqueda de Plasma/KRunner, búsquedas web y recientes | Configurar nuestro lanzador y, si se desea, un indexador; no copiar ajustes de Plasma sin consumidor |
| Región | Idioma, formatos, fecha, zona horaria, corrección ortográfica | NixOS para valores del sistema; ajustes específicos de aplicaciones cuando corresponda |
| Accesibilidad | Lector de pantalla, teclas especiales, efectos visuales y ayudas de entrada | Evaluar por función; parte depende del compositor y parte de servicios externos |
| Usuarios y credenciales | Usuarios, contraseñas, KDE Wallet y cuentas cuando estén instaladas | Herramientas existentes; cuentas y servicios declarativos mediante NixOS |
| Impresión | Impresoras y colas | CUPS y su interfaz existente |
| Discos y dispositivos | Automontaje, acciones al conectar, USB y almacenamiento | UDisks/herramientas existentes; distinguir preferencias del usuario de políticas del sistema |
| Compartir | Escritorio remoto y recursos compartidos | Herramientas compatibles con Hyprland; el servidor de escritorio remoto de KWin no es intercambiable |
| Sistema | Actualizaciones, información de hardware, sensores, seguridad de firmware y estadísticas | NixOS para actualizaciones; reutilizar diagnósticos existentes |

Inventario agrupado a partir de los módulos locales y de la
[documentación de KDE](https://docs.kde.org/trunk_kf6/en/systemsettings/systemsettings/general.html).
Las páginas visibles dependen de paquetes, hardware y sesión.

## Estado comprobado en esta máquina

- Monitor externo CORSAIR 27QHD240, conectado por DP-3, 2560×1440.
- `/sys/class/backlight` vacío. No hay una pantalla controlable mediante esa API.
- No se encontraron nodos `/dev/i2c-*`. Hay buses I2C en sysfs, pero falta exponer
  y comprobar el acceso de usuario antes de probar DDC/CI. No se ha confirmado
  que este monitor acepte el control de brillo por DDC/CI.
- power-profiles-daemon y UPower están activos. `powerprofilesctl list` devuelve
  performance, balanced y power-saver; balanced está seleccionado. El controlador
  de CPU es amd_pstate y performance no se anuncia degradado.
- hypridle está activo; plasma-powerdevil está inactivo en esta sesión.
- logind informa `IdleAction=ignore`; no se encontraron temporizadores de
  apagado/suspensión ni ajustes de reinicio automático en la configuración revisada.
- hypridle bloquea a los 600 segundos y apaga la pantalla a los 900. No tiene
  un listener de suspensión automática.
- logind devuelve `yes` para CanSuspend y CanHibernate. Esto anuncia capacidad,
  no demuestra una reanudación correcta. `/sys/power/resume` es `0:0`: hibernación
  requiere una revisión separada antes de presentarla como lista para usar.
- No se cambió el brillo ni el perfil de energía ni se suspendió el equipo.

## Cómo ampliar HyprMod

Se inspeccionó el código de HyprMod 0.4.0 que empaquetamos, commit
`ffd47d804d8996cf3852dbb7ca1c949c424a57fb`.

Es Python con GTK4/libadwaita. `hyprmod/window.py` registra páginas y
`hyprmod/ui/sidebar.py` organiza la navegación. Podemos añadir páginas y sus
servicios mediante un parche en `packages/hyprmod/default.nix`.

No se encontró una API pública para cargar páginas externas. La página
`hyprmod/pages/plugins.py` edita opciones de plugins del compositor; no es un
sistema de extensiones del centro de ajustes.

El [roadmap](https://github.com/BlueManCZ/hyprmod#-roadmap) prevé hypridle,
hyprlock e hyprpaper. Declara fuera de alcance Wi-Fi, Bluetooth, impresión,
aplicaciones predeterminadas y temas GTK. Por ello, nuestra ampliación de
ajustes generales se mantendría localmente; no debemos asumir aceptación
upstream. Hay que comprobar el parche y sus callbacks GTK al actualizar.

## Primera fase propuesta

1. **Energía**: selector de los perfiles realmente disponibles, estado actual,
   explicación de restricciones y actualización cuando cambien fuera del panel.
   Usar la [API de power-profiles-daemon](https://upower.pages.freedesktop.org/power-profiles-daemon/gdbus-org.freedesktop.UPower.PowerProfiles.html).
2. **Suspensión y pantalla**: tiempos separados para atenuar, apagar pantalla,
   bloquear y suspender; opción Nunca; botón Suspender ahora; modo presentación
   temporal. Respetar inhibidores y bloquear antes de suspender. Usar
   [hypridle](https://wiki.hypr.land/Hypr-Ecosystem/hypridle/) y
   [logind](https://systemd.io/WRITING_DESKTOP_ENVIRONMENTS/).
3. **Brillo**: detección de pantallas y control por monitor. En este equipo,
   preparar I2C/DDC de forma declarativa, comprobar capacidades y lectura del
   brillo, y solo después habilitar el deslizador. Usar
   [ddcutil/libddcutil](https://www.ddcutil.com/); ddcui es una interfaz existente
   que sirve como alternativa inicial. Un filtro de oscurecimiento por software
   no equivale al brillo físico y no debe presentarse como si lo fuera.
4. **Detalles de energía**: batería/UPS si existen, aplicaciones que impiden la
   suspensión y comportamiento del botón de encendido/tapa cuando sea aplicable.
   Algunas políticas de logind requieren configuración del sistema.

El acceso I2C se puede preparar mediante el módulo `hardware.i2c` de nuestro
Nixpkgs fijado; deben revisarse sus reglas de acceso para la sesión activa.
No se ha activado en este análisis.

## UX y persistencia

Mantener el engranaje y Super+, como entrada única. Añadir las secciones
Pantallas y brillo, Energía y suspensión, y Accesos a otros ajustes. Para red,
Bluetooth, audio e impresión, abrir las aplicaciones existentes con navegación
clara, sin prometer que son páginas incrustadas.

Los controles deben mostrar valores reales y guardar de forma explícita lo que
es persistente. Los archivos de hypridle/hyprlock deben seguir enlazados al repo.
Los cambios en servicios, permisos o políticas de arranque se guardan en Nix y
se aplican con el flujo de rebuild. Un ajuste en vivo por D-Bus/DDC no queda
declarado en Git por sí solo: hay que diseñar su persistencia, incluida la
reconexión del monitor si se quiere restaurar el brillo.

Las páginas de sistema necesitan su propio ciclo de leer/aplicar/guardar y no
deben escribir valores de energía dentro de `hyprland-gui.lua`. El deshacer de
HyprMod no puede prometer revertir una acción como suspender el equipo.

Se revisó también [nwg-shell-config](https://github.com/nwg-piotr/nwg-shell-config).
Ofrece ajustes más amplios, pero está orientado a su propio conjunto de
componentes y archivos. Su compatibilidad con nuestra configuración Lua debe
validarse; no es un reemplazo directo que garantice cubrir estas necesidades.

Recomendación: ampliar HyprMod con las dos páginas básicas y aprovechar los
servicios y aplicaciones existentes, manteniendo la ampliación acotada.
