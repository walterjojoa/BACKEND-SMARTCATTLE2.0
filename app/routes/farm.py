from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import Settings
from app.dependencies import (
    Clock,
    OwnerUser,
    Visible,
    get_app_settings,
    get_clock,
    get_farm_pairings,
    get_farm_services,
    reporter_account,
)
from app.schemas.camera import CameraPairing
from app.schemas.farm_pc import FarmPcKey, FarmPcPairing, FarmPcPresence, FarmPcState
from app.services.camera_pairing import LIFETIME, CameraPairings
from app.services.farm_agents import FarmServices, farm_key

router = APIRouter(tags=["farm PC"])


@router.post("/api/farm-pc/pairing", response_model=CameraPairing, status_code=status.HTTP_201_CREATED)
def start_farm_pc_pairing(
    owner: OwnerUser,
    pairings: CameraPairings = Depends(get_farm_pairings),
    clock: Clock = Depends(get_clock),
) -> CameraPairing:
    """A code short enough to type on the farm's PC, which links it to this account."""
    return CameraPairing(code=pairings.issue_short(owner.account_id, clock()), expires_in=int(LIFETIME.total_seconds()))


@router.post("/api/farm-pc/paired", response_model=FarmPcKey, status_code=status.HTTP_201_CREATED)
def pair_farm_pc(
    data: FarmPcPairing,
    pairings: CameraPairings = Depends(get_farm_pairings),
    settings: Settings = Depends(get_app_settings),
    clock: Clock = Depends(get_clock),
) -> FarmPcKey:
    """Gives the PC its key. Needs the code instead of a session, as the PC has neither browser nor login."""
    if settings.jwt_secret is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Accounts are switched off")
    account_id = pairings.redeem(data.code.strip().upper(), clock())
    if account_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This code has expired; show a new one")
    return FarmPcKey(key=farm_key(account_id, settings.jwt_secret.get_secret_value()), origins=settings.cors_origins)


@router.put("/api/ai/farm-pc", status_code=status.HTTP_204_NO_CONTENT)
def report_farm_pc(
    data: FarmPcPresence,
    account_id: int | None = Depends(reporter_account),
    services: FarmServices = Depends(get_farm_services),
    clock: Clock = Depends(get_clock),
) -> None:
    """Where this PC can be reached now. Its address changes when its tunnel restarts.

    With the deployment's shared key instead of a farm key, it is the service every account without a PC of its
    own uses: anyone who signs in can then broadcast a phone or open a camera with a public address.
    """
    now = clock()
    if account_id is None:
        services.report_shared(str(data.url).rstrip("/"), now)
        return
    media_url = None if data.media_url is None else str(data.media_url).rstrip("/")
    services.report(account_id, str(data.url).rstrip("/"), now, media_url)


@router.get("/api/ai/farm-pc/access", status_code=status.HTTP_204_NO_CONTENT)
def farm_pc_access(scope: Visible, account_id: int | None = Depends(reporter_account)) -> None:
    """Whether the person signed in belongs to this PC's account. Only they may look around its network."""
    if account_id is None or scope.account_id != account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This PC belongs to another account")


@router.get("/api/farm-pc", response_model=FarmPcState)
def get_farm_pc(
    scope: Visible,
    services: FarmServices = Depends(get_farm_services),
    settings: Settings = Depends(get_app_settings),
    clock: Clock = Depends(get_clock),
) -> FarmPcState:
    """This account's PC, and the shared service it can use while it has none.

    SMARTCATTLE_AI_URL was reaching nobody. /health said whether it was
    configured and nothing handed over the address, so a browser with no PC
    linked had nowhere to send video to: the "Transmitir" button stayed grey
    with no way to find out why. Kept as its own field rather than folded into
    `url`, because the page asks `url` whether this account can reach cameras
    on its own network, and the shared service answers no to that.
    """
    now = clock()
    configured = str(settings.smartcattle_ai_url) if settings.smartcattle_ai_url else None
    return FarmPcState(
        url=services.url_for(scope.account_id, now),
        # The one that reported itself is alive right now; the configured one is only a promise.
        service_url=services.shared_url(now) or configured,
    )
