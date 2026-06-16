#!/usr/bin/env bash
set -Eeuo pipefail

# Deploy tk-live admin backend with an existing conda installation.
#
# Default assumptions:
# - Backend path: /www/app/ai-live-admin-backend
# - Conda env: tk-live-admin
# - Backend binds: 127.0.0.1:8100
# - PostgreSQL is already installed and DATABASE_URL is configured in backend/.env
#
# Usage:
#   sudo bash deploy_backend_conda.sh
#
# Optional env overrides:
#   BACKEND_DIR=/www/app/ai-live-admin-backend
#   PROJECT_DIR=/opt/tk-live
#   CONDA_ENV_NAME=tk-live-admin
#   PYTHON_VERSION=3.12
#   BACKEND_HOST=127.0.0.1
#   BACKEND_PORT=8100
#   SERVICE_NAME=tk-live-admin-backend

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-}"
BACKEND_DIR="${BACKEND_DIR:-}"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-tk-live-admin}"
PYTHON_VERSION="${PYTHON_VERSION:-3.12}"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8100}"
SERVICE_NAME="${SERVICE_NAME:-tk-live-admin-backend}"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

resolve_backend_dir() {
  if [[ -n "$BACKEND_DIR" ]]; then
    printf '%s\n' "$BACKEND_DIR"
    return
  fi

  if [[ -n "$PROJECT_DIR" ]]; then
    if [[ -f "$PROJECT_DIR/pyproject.toml" ]]; then
      printf '%s\n' "$PROJECT_DIR"
      return
    fi
  fi

  if [[ -f "/www/app/ai-live-admin-backend/pyproject.toml" ]]; then
    printf '%s\n' "/www/app/ai-live-admin-backend"
    return
  fi

  if [[ -f "$SCRIPT_DIR/../backend/pyproject.toml" ]]; then
    cd "$SCRIPT_DIR/../backend" && pwd
    return
  fi

  if [[ -f "$PWD/pyproject.toml" ]]; then
    pwd
    return
  fi
}

log() {
  printf '\n[%s] %s\n' "$(date '+%F %T')" "$*"
}

fail() {
  printf '\nERROR: %s\n' "$*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "缺少命令：$1"
}

if [[ "$(id -u)" -ne 0 ]]; then
  fail "请使用 root 运行，例如：sudo BACKEND_DIR=/www/app/ai-live-admin-backend bash deploy_backend_conda.sh"
fi

require_cmd systemctl
require_cmd curl

BACKEND_DIR="$(resolve_backend_dir || true)"
if [[ -z "${BACKEND_DIR:-}" ]]; then
  fail "无法定位后端目录。请指定：sudo BACKEND_DIR=/www/app/ai-live-admin-backend bash deploy_backend_conda.sh"
fi

if [[ ! -d "$BACKEND_DIR" ]]; then
  fail "后端目录不存在：$BACKEND_DIR"
fi

if [[ ! -f "$BACKEND_DIR/pyproject.toml" ]]; then
  fail "未找到 $BACKEND_DIR/pyproject.toml"
fi

find_conda() {
  if command -v conda >/dev/null 2>&1; then
    command -v conda
    return
  fi

  local candidates=(
    "$HOME/miniconda3/bin/conda"
    "$HOME/anaconda3/bin/conda"
    "/root/miniconda3/bin/conda"
    "/root/anaconda3/bin/conda"
    "/opt/conda/bin/conda"
  )

  for candidate in "${candidates[@]}"; do
    if [[ -x "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return
    fi
  done
}

CONDA_BIN="$(find_conda || true)"
if [[ -z "${CONDA_BIN:-}" ]]; then
  fail "未找到 conda。请确认服务器已安装 conda，并把 conda 加入 PATH。"
fi

CONDA_BASE="$("$CONDA_BIN" info --base)"
CONDA_SH="$CONDA_BASE/etc/profile.d/conda.sh"
if [[ ! -f "$CONDA_SH" ]]; then
  fail "未找到 conda 初始化脚本：$CONDA_SH"
fi

# shellcheck disable=SC1090
source "$CONDA_SH"

log "使用 conda：$CONDA_BIN"
log "后端目录：$BACKEND_DIR"

if ! conda env list | awk '{print $1}' | grep -qx "$CONDA_ENV_NAME"; then
  log "创建 conda 环境：$CONDA_ENV_NAME Python $PYTHON_VERSION"
  conda create -y -n "$CONDA_ENV_NAME" "python=$PYTHON_VERSION"
else
  log "conda 环境已存在：$CONDA_ENV_NAME"
fi

conda activate "$CONDA_ENV_NAME"

log "升级 pip 并安装后端依赖"
python -m pip install --upgrade pip
python -m pip install -e "$BACKEND_DIR"

if [[ ! -f "$BACKEND_DIR/.env" ]]; then
  log "未发现 .env，复制 .env.example"
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
  chmod 600 "$BACKEND_DIR/.env"
  printf '\n已创建 %s，请确认 DATABASE_URL、SECRET_KEY、INITIAL_ADMIN_PASSWORD、INTEGRATION_API_KEY 后再正式使用。\n' "$BACKEND_DIR/.env"
fi

log "数据库迁移：检测当前状态"
cd "$BACKEND_DIR"

# 自适应预检：历史上线上靠 startup 的 create_all 建表，可能没有 alembic 版本记录。
# 直接 upgrade 会因为 001 的列已存在而报错，这里先判断库的真实状态再决定 stamp / upgrade。
MIGRATE_STATE="$(python - <<'PY'
import sys

try:
    from sqlalchemy import create_engine, inspect

    from app.core.config import get_settings

    insp = inspect(create_engine(get_settings().database_url))
    tables = set(insp.get_table_names())
    if "alembic_version" in tables:
        state = "UPGRADE"
    elif "quota_grants" in tables:
        cols = {c["name"] for c in insp.get_columns("quota_grants")}
        if "consumed" in cols:
            # quota_grants 已是新结构，只需标记版本
            state = "STAMP_HEAD"
        else:
            # 旧结构 quota_grants（create_all 建出，缺 consumed/multiplier）：
            # 标记到 002 再 upgrade，让 003 幂等补列
            state = "STAMP_002"
    elif "users" in tables and "consumption_multiplier" in {
        c["name"] for c in insp.get_columns("users")
    }:
        # 001 的列已存在但没有版本记录：先打 001 基线，再升级
        state = "STAMP_001"
    else:
        # 全新库或比 001 更早的库：从头正常升级
        state = "FRESH"
    print(state)
except Exception as exc:  # noqa: BLE001
    sys.stderr.write(f"migrate precheck error: {exc}\n")
    print("ERROR")
PY
)"

case "$MIGRATE_STATE" in
  UPGRADE|FRESH)
    log "执行 alembic upgrade head（状态：$MIGRATE_STATE）"
    python -m alembic upgrade head
    ;;
  STAMP_001)
    log "历史库无版本记录：先 stamp 到 001 基线，再 upgrade head"
    python -m alembic stamp 001_add_user_quota
    python -m alembic upgrade head
    ;;
  STAMP_002)
    log "检测到旧结构 quota_grants：先 stamp 到 002，再 upgrade head（由 003 幂等补列）"
    python -m alembic stamp 002_add_quota_grants
    python -m alembic upgrade head
    ;;
  STAMP_HEAD)
    log "所有表已存在但无版本记录：stamp 到最新版本（不执行 DDL）"
    python -m alembic stamp head
    ;;
  *)
    fail "数据库迁移预检失败，请确认 $BACKEND_DIR/.env 的 DATABASE_URL 正确且数据库可连接"
    ;;
esac

log "当前数据库版本"
python -m alembic current || true

log "写入 systemd 服务：$SERVICE_FILE"
cat >"$SERVICE_FILE" <<EOF
[Unit]
Description=tk-live admin backend
After=network.target postgresql.service

[Service]
Type=simple
WorkingDirectory=$BACKEND_DIR
ExecStart=$CONDA_BASE/envs/$CONDA_ENV_NAME/bin/python -m uvicorn app.main:app --host $BACKEND_HOST --port $BACKEND_PORT
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

log "启动 systemd 服务"
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

log "等待服务启动"
sleep 3

if systemctl is-active --quiet "$SERVICE_NAME"; then
  log "服务已启动：$SERVICE_NAME"
else
  systemctl status "$SERVICE_NAME" --no-pager || true
  fail "服务启动失败，请查看：journalctl -u $SERVICE_NAME -n 100"
fi

log "健康检查：http://$BACKEND_HOST:$BACKEND_PORT/health"
if curl -fsS "http://$BACKEND_HOST:$BACKEND_PORT/health" >/tmp/tk-live-admin-health.json; then
  cat /tmp/tk-live-admin-health.json
  printf '\n'
else
  fail "健康检查失败，请查看：journalctl -u $SERVICE_NAME -n 100"
fi

log "部署完成"
printf '查看日志：journalctl -u %s -f\n' "$SERVICE_NAME"