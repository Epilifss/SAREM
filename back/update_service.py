import hashlib
import os
import subprocess
import sys
import tempfile
import time
import tkinter as tk

import requests
import ttkbootstrap as tb
from tkinter import messagebox

from back.utils import center_window_screen, get_config_path, resource_path
from front import versao

VERSAO_ATUAL = versao

# Novo endpoint recomendado (manifesto JSON)
URL_MANIFEST = "https://dl.dropboxusercontent.com/scl/fi/r2qudjfm7eymdf7icjd5z/update_manifest.json?rlkey=vto3ketxqqmfrwxh3iu31ndkm&st=ijmaig8s&dl=0"

# Compatibilidade com o fluxo atual (fallback txt)
URL_VERSAO = "https://dl.dropboxusercontent.com/scl/fi/dh936k1ph0m2eq5low9gn/versao.txt?rlkey=fnyxw89yee7ai571ue3znbaiv&st=xd9f26ij&dl=0"
URL_LINK_TXT = "https://dl.dropboxusercontent.com/scl/fi/9hu4p9wo6ydqiit7zfp1b/linknovaversao.txt?rlkey=yubwve92t8qpr2bxd13lsvqij&st=vs0ddwfv&dl=0"

REQUEST_TIMEOUT = 8
REQUEST_RETRIES = 3
UPDATE_LOCK = os.path.join(tempfile.gettempdir(), "sarem_update.lock")


def _update_log_path():
    config_path = get_config_path()
    base_dir = os.path.dirname(config_path)
    return os.path.join(base_dir, "update.log")


def _log_update(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}\n"
    try:
        with open(_update_log_path(), "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception:
        pass


def _parse_version(version_str):
    clean = (version_str or "").strip()
    if not clean:
        return (0,)
    parts = []
    for token in clean.replace("-", ".").split("."):
        digits = "".join(ch for ch in token if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def _is_newer_version(remote_version, current_version):
    return _parse_version(remote_version) > _parse_version(current_version)


def _http_get(url, stream=False):
    last_exc = None
    for tentativa in range(1, REQUEST_RETRIES + 1):
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT, stream=stream)
            if response.status_code == 200:
                return response
            _log_update(f"HTTP {response.status_code} ao acessar {url} (tentativa {tentativa}).")
        except Exception as exc:
            last_exc = exc
            _log_update(f"Falha HTTP ao acessar {url} (tentativa {tentativa}): {exc}")
        time.sleep(0.5)
    if last_exc:
        raise last_exc
    return None


def _normalize_manifest(raw):
    if not raw:
        return None

    version = str(raw.get("version", "")).strip()
    installer_url = str(raw.get("installer_url", "")).strip()
    if not version or not installer_url:
        return None

    notes = raw.get("release_notes", "")
    if isinstance(notes, list):
        notes = "\n".join(f"- {n}" for n in notes)
    notes = str(notes).strip()

    silent_args = str(raw.get("silent_args", "/SP- /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /CLOSEAPPLICATIONS")).strip()
    if "/SUPPRESSMSGBOXES" not in silent_args.upper():
        silent_args = f"{silent_args} /SUPPRESSMSGBOXES".strip()

    return {
        "version": version,
        "installer_url": installer_url,
        "sha256": str(raw.get("sha256", "")).strip().lower(),
        "size": int(raw.get("size", 0) or 0),
        "mandatory": bool(raw.get("mandatory", False)),
        "silent_args": silent_args,
        "create_backup": bool(raw.get("create_backup", False)),
        "keep_backup_on_success": bool(raw.get("keep_backup_on_success", False)),
        "release_notes": notes,
    }


def _get_manifest():
    # Tenta o modelo novo (JSON)
    try:
        response = _http_get(URL_MANIFEST, stream=False)
        if response is not None:
            raw_manifest = response.json()
            manifest = _normalize_manifest(raw_manifest)
            if manifest:
                _log_update("Manifesto JSON carregado com sucesso.")
                return manifest
    except Exception as exc:
        _log_update(f"Falha ao ler manifesto JSON: {exc}")

    # Fallback: modelo antigo em TXT
    try:
        response_version = _http_get(URL_VERSAO, stream=False)
        response_link = _http_get(URL_LINK_TXT, stream=False)
        if response_version is None or response_link is None:
            return None

        manifest = _normalize_manifest({
            "version": response_version.text.strip(),
            "installer_url": response_link.text.strip(),
            "mandatory": False,
            "release_notes": "Nova versao disponivel.",
        })
        if manifest:
            _log_update("Manifesto fallback TXT carregado com sucesso.")
        return manifest
    except Exception as exc:
        _log_update(f"Falha ao montar manifesto via TXT: {exc}")
        return None


def _sha256_file(file_path):
    hash_obj = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest().lower()


def _download_installer(parent, manifest):
    installer_url = manifest["installer_url"]
    expected_size = manifest["size"]

    progress_win = tk.Toplevel(parent)
    progress_win.title("Baixando atualizacao")
    progress_win.iconbitmap(resource_path("SAREM.ico"))
    progress_win.geometry("420x130")
    progress_win.transient(parent)
    progress_win.grab_set()

    label = tb.Label(progress_win, text=f"Baixando versao {manifest['version']}...")
    label.pack(pady=(10, 5))

    progress = tb.Progressbar(progress_win, orient="horizontal", length=360, mode="determinate")
    progress.pack(pady=8)

    status = tb.Label(progress_win, text="Iniciando download...")
    status.pack(pady=(0, 8))

    center_window_screen(progress_win, 420, 130)

    response = _http_get(installer_url, stream=True)
    if response is None:
        progress_win.destroy()
        raise RuntimeError("Nao foi possivel iniciar o download do instalador.")

    total = int(response.headers.get("content-length", 0))
    if total <= 0 and expected_size > 0:
        total = expected_size

    temp_dir = tempfile.gettempdir()
    installer_path = os.path.join(temp_dir, f"sarem_update_{manifest['version']}.exe")
    downloaded = 0

    with open(installer_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue
            f.write(chunk)
            downloaded += len(chunk)

            if total > 0:
                progress["value"] = (downloaded / total) * 100
                status.config(text=f"{downloaded / (1024 * 1024):.1f} MB / {total / (1024 * 1024):.1f} MB")
            else:
                status.config(text=f"{downloaded / (1024 * 1024):.1f} MB baixados")

            progress_win.update_idletasks()

    progress_win.destroy()

    if expected_size > 0 and os.path.getsize(installer_path) != expected_size:
        raise RuntimeError("Tamanho do arquivo baixado difere do manifesto.")

    expected_hash = manifest.get("sha256") or ""
    if expected_hash:
        current_hash = _sha256_file(installer_path)
        if current_hash != expected_hash:
            raise RuntimeError("Falha na validacao de integridade (SHA-256).")

    return installer_path


def _current_app_paths():
    frozen = bool(getattr(sys, "frozen", False))
    if frozen:
        app_exe = os.path.abspath(sys.executable)
        app_dir = os.path.dirname(app_exe)
        return app_dir, app_exe

    # Em ambiente de desenvolvimento, nao ha exe instalado para restaurar/reiniciar.
    return os.path.abspath("."), ""


def _schedule_transactional_update(installer_path, manifest):
    pid = os.getpid()
    silent_args = manifest["silent_args"]
    create_backup = False
    keep_backup = manifest.get("keep_backup_on_success", False)

    app_dir, app_exe = _current_app_paths()
    temp_root = tempfile.gettempdir()
    stamp = time.strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(temp_root, f"sarem_backup_{stamp}")
    helper_ps1 = os.path.join(temp_root, f"sarem_apply_update_{stamp}.ps1")
    apply_log = os.path.join(os.path.dirname(get_config_path()), "update_apply.log")

    ps_script = f"""
param(
    [int]$TargetPid,
    [string]$InstallerPath,
    [string]$InstallerArgs,
    [string]$AppDir,
    [string]$AppExe,
    [string]$BackupDir,
    [string]$LogPath,
    [int]$CreateBackup,
    [int]$KeepBackup
)

$ErrorActionPreference = 'Stop'

function Write-Log([string]$Message) {{
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $LogPath -Value "[$ts] $Message"
}}

function Wait-TargetProcess([int]$PidToWait, [int]$TimeoutSeconds) {{
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ($true) {{
        $p = Get-Process -Id $PidToWait -ErrorAction SilentlyContinue
        if (-not $p) {{ break }}

        if ((Get-Date) -gt $deadline) {{
            Write-Log "Timeout aguardando processo $PidToWait. Tentando encerrar aplicacao."
            try {{
                $p.CloseMainWindow() | Out-Null
                Start-Sleep -Seconds 5
            }}
            catch {{}}

            $p = Get-Process -Id $PidToWait -ErrorAction SilentlyContinue
            if ($p) {{
                Stop-Process -Id $PidToWait -Force -ErrorAction SilentlyContinue
                Write-Log "Processo $PidToWait encerrado forcadamente para aplicar update."
            }}
            break
        }}

        Start-Sleep -Seconds 1
    }}
}}

function Run-Robocopy([string]$From, [string]$To) {{
    New-Item -ItemType Directory -Path $To -Force | Out-Null
    robocopy $From $To /MIR /R:2 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -gt 7) {{
        throw "Robocopy falhou com codigo $LASTEXITCODE (de '$From' para '$To')."
    }}
}}

try {{
    Write-Log "Updater iniciado. Aguardando encerramento do processo $TargetPid."
    Wait-TargetProcess -PidToWait $TargetPid -TimeoutSeconds 10

    $canRollback = $false
    if ($CreateBackup -eq 1) {{
        Write-Log "Iniciando backup de $AppDir para $BackupDir"
        Run-Robocopy -From $AppDir -To $BackupDir
        $canRollback = $true
        Write-Log "Backup concluido."
    }}

    Write-Log "Executando instalador silencioso: $InstallerPath $InstallerArgs"
    $p = Start-Process -FilePath $InstallerPath -ArgumentList $InstallerArgs -Wait -PassThru
    if ($p.ExitCode -ne 0) {{
        throw "Instalador finalizou com codigo de saida $($p.ExitCode)."
    }}
    Write-Log "Instalacao concluida com sucesso."

    if ((Test-Path $InstallerPath)) {{
        Remove-Item $InstallerPath -Force -ErrorAction SilentlyContinue
    }}

    if (($CreateBackup -eq 1) -and ($KeepBackup -ne 1) -and (Test-Path $BackupDir)) {{
        Remove-Item $BackupDir -Recurse -Force -ErrorAction SilentlyContinue
        Write-Log "Backup removido apos sucesso."
    }}

    if ($AppExe -and (Test-Path $AppExe)) {{
        Start-Process -FilePath $AppExe | Out-Null
        Write-Log "Aplicacao reiniciada apos update."
    }}
}}
catch {{
    Write-Log "Falha no update: $($_.Exception.Message)"
    try {{
        if (($CreateBackup -eq 1) -and (Test-Path $BackupDir)) {{
            Write-Log "Iniciando rollback a partir de $BackupDir"
            Run-Robocopy -From $BackupDir -To $AppDir
            Write-Log "Rollback concluido com sucesso."
        }}
    }}
    catch {{
        Write-Log "Falha durante rollback: $($_.Exception.Message)"
    }}

    if ($AppExe -and (Test-Path $AppExe)) {{
        Start-Process -FilePath $AppExe | Out-Null
        Write-Log "Aplicacao reiniciada apos tentativa de rollback."
    }}
}}
finally {{
    Remove-Item $MyInvocation.MyCommand.Path -Force -ErrorAction SilentlyContinue
}}
""".strip()

    with open(helper_ps1, "w", encoding="utf-8") as f:
        f.write(ps_script)

    ps_cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        helper_ps1,
        "-TargetPid",
        str(pid),
        "-InstallerPath",
        installer_path,
        "-InstallerArgs",
        silent_args,
        "-AppDir",
        app_dir,
        "-AppExe",
        app_exe,
        "-BackupDir",
        backup_dir,
        "-LogPath",
        apply_log,
        "-CreateBackup",
        "1" if create_backup else "0",
        "-KeepBackup",
        "1" if keep_backup else "0",
    ]

    creation_flags = 0
    if os.name == "nt":
        creation_flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0)

    subprocess.Popen(ps_cmd, creationflags=creation_flags)


def _show_installing_notice(parent, version):
    notice = tk.Toplevel(parent)
    notice.title("Atualizacao")
    notice.iconbitmap(resource_path("SAREM.ico"))
    notice.geometry("420x130")
    notice.transient(parent)
    notice.resizable(False, False)

    label = tb.Label(notice, text=f"Instalando versao {version} em segundo plano...")
    label.pack(pady=(18, 8))

    progress = tb.Progressbar(notice, orient="horizontal", length=340, mode="indeterminate")
    progress.pack(pady=8)
    progress.start(12)

    status = tb.Label(notice, text="O SAREM sera fechado automaticamente.")
    status.pack(pady=(0, 8))

    center_window_screen(notice, 420, 130)
    notice.update_idletasks()
    return notice


def _close_app_for_update(parent, delay_ms=100):
    try:
        parent.after(delay_ms, parent.destroy)
    except Exception:
        try:
            parent.destroy()
        except Exception:
            pass


def _acquire_lock():
    try:
        fd = os.open(UPDATE_LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode("utf-8"))
        os.close(fd)
        return True
    except FileExistsError:
        _log_update("Verificacao de update ignorada: lock ativo.")
        return False
    except Exception as exc:
        _log_update(f"Falha ao adquirir lock de update: {exc}")
        return False


def _release_lock():
    try:
        if os.path.exists(UPDATE_LOCK):
            os.remove(UPDATE_LOCK)
    except Exception:
        pass


def _prompt_update(manifest):
    notes = manifest.get("release_notes", "")
    mandatory = manifest.get("mandatory", False)

    msg = f"Nova versao disponivel: {manifest['version']}\n\n"
    if notes:
        msg += f"Novidades:\n{notes}\n\n"

    if mandatory:
        messagebox.showinfo("SAREM - Atualizacao obrigatoria", msg + "A atualizacao sera iniciada agora.")
        return True

    return messagebox.askyesno("SAREM - Atualizacao disponivel", msg + "Deseja atualizar agora?")


def verificar_e_att(parent):
    if not _acquire_lock():
        return True

    try:
        manifest = _get_manifest()
        if not manifest:
            return True

        remote_version = manifest["version"]
        if not _is_newer_version(remote_version, VERSAO_ATUAL):
            return True

        if not _prompt_update(manifest):
            _log_update(f"Usuario recusou a atualizacao {remote_version}. O aviso sera exibido novamente na proxima abertura.")
            return True

        try:
            installer_path = _download_installer(parent, manifest)
        except Exception as exc:
            _log_update(f"Falha no download/validacao: {exc}")
            messagebox.showerror("Erro", f"Falha ao baixar/validar a atualizacao:\n{exc}")
            return True

        try:
            _schedule_transactional_update(installer_path, manifest)
            _log_update(f"Atualizacao {remote_version} agendada com sucesso.")
            _show_installing_notice(parent, remote_version)
            _close_app_for_update(parent, delay_ms=1800)
            return False
        except Exception as exc:
            _log_update(f"Falha ao agendar atualizacao silenciosa: {exc}")
            messagebox.showerror("Erro", f"Nao foi possivel iniciar a instalacao automatica:\n{exc}")
            return True
    finally:
        _release_lock()
