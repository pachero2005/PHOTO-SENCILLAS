[app]

title = PY REPOSITORIO
package.name = pyrepositorio
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json
version = 0.1.0
requirements = python3,kivy,pillow
orientation = portrait
fullscreen = 0

android.permissions = CAMERA,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 23
android.ndk = 25b
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
