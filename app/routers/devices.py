"""Read-only catalog of configured WhatsApp devices.

Devices are defined in configuration (``DEVICE_ID`` / ``DEVICES``); this
endpoint just exposes them so the dashboard can offer source/target device
pickers when assigning bots. There is no create/delete here by design —
device lifecycle (QR login, etc.) stays on the GoWA gateway.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import Settings
from app.deps import require_auth, settings_dep
from app.schemas import DeviceInfo

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("", response_model=list[DeviceInfo])
def list_devices(
    settings: Settings = Depends(settings_dep),
    _: object = Depends(require_auth),
) -> list[DeviceInfo]:
    default = settings.default_device_id
    return [
        DeviceInfo(id=d.id, label=d.display_label, is_default=(d.id == default))
        for d in settings.resolved_devices
    ]
