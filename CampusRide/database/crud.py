from database.engine import async_session
from database.models import Passenger, RideLobby, RideStatus, User
from sqlalchemy import select
from sqlalchemy.orm import selectinload


async def get_user(user_id: int) -> User | None:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()


async def create_or_update_user(
    user_id: int,
    username: str | None,
    full_name: str,
    room_number: str,
    sbp_phone: str,
    sbp_bank: str,
):
    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            user = User(
                id=user_id,
                username=username,
                full_name=full_name,
                room_number=room_number,
                sbp_phone=sbp_phone,
                sbp_bank=sbp_bank,
            )
            session.add(user)
        else:
            user.username = username
            user.full_name = full_name
            user.room_number = room_number
            user.sbp_phone = sbp_phone
            user.sbp_bank = sbp_bank
        await session.commit()
        return user


async def create_lobby(
    host_id: int,
    from_loc: str,
    to_loc: str,
    meeting: str,
    dep_time: str,
    seats: int,
) -> RideLobby:
    async with async_session() as session:
        lobby = RideLobby(
            host_id=host_id,
            from_location=from_loc,
            to_location=to_loc,
            meeting_point=meeting,
            departure_time=dep_time,
            max_seats=seats,
            status=RideStatus.OPEN,
        )
        session.add(lobby)
        await session.commit()
        await session.refresh(lobby)
        return lobby


async def get_active_lobbies() -> list[RideLobby]:
    async with async_session() as session:
        query = (
            select(RideLobby)
            .where(RideLobby.status.in_([RideStatus.OPEN, RideStatus.FULL]))
            .options(
                selectinload(RideLobby.host),
                selectinload(RideLobby.passengers).selectinload(Passenger.user),
            )
            .order_by(RideLobby.created_at.desc())
        )
        result = await session.execute(query)
        return list(result.scalars().all())


async def get_lobby_by_id(lobby_id: int) -> RideLobby | None:
    async with async_session() as session:
        query = (
            select(RideLobby)
            .where(RideLobby.id == lobby_id)
            .options(
                selectinload(RideLobby.host),
                selectinload(RideLobby.passengers).selectinload(Passenger.user),
            )
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()


async def add_passenger(lobby_id: int, user_id: int) -> bool:
    async with async_session() as session:
        lobby = await session.get(
            RideLobby, lobby_id, options=[selectinload(RideLobby.passengers)]
        )
        if not lobby or lobby.status != RideStatus.OPEN:
            return False

        if lobby.host_id == user_id:
            return False

        for p in lobby.passengers:
            if p.user_id == user_id:
                return False

        passenger = Passenger(lobby_id=lobby_id, user_id=user_id)
        session.add(passenger)
        lobby.passengers.append(passenger)

        if len(lobby.passengers) >= lobby.max_seats:
            lobby.status = RideStatus.FULL

        await session.commit()
        return True


async def remove_passenger(lobby_id: int, user_id: int) -> bool:
    async with async_session() as session:
        query = select(Passenger).where(
            Passenger.lobby_id == lobby_id, Passenger.user_id == user_id
        )
        result = await session.execute(query)
        passenger = result.scalar_one_or_none()
        if passenger:
            await session.delete(passenger)
            lobby = await session.get(
                RideLobby,
                lobby_id,
                options=[selectinload(RideLobby.passengers)],
            )
            if lobby and lobby.status == RideStatus.FULL:
                lobby.status = RideStatus.OPEN
            await session.commit()
            return True
        return False


async def update_lobby_status(
    lobby_id: int, status: RideStatus, cost: float = None
):
    async with async_session() as session:
        lobby = await session.get(RideLobby, lobby_id)
        if lobby:
            lobby.status = status
            if cost is not None:
                lobby.total_cost = cost
            await session.commit()


async def set_passenger_paid_status(
    lobby_id: int, user_id: int, status: int
) -> bool:
    async with async_session() as session:
        query = select(Passenger).where(
            Passenger.lobby_id == lobby_id, Passenger.user_id == user_id
        )
        result = await session.execute(query)
        p = result.scalar_one_or_none()
        if p:
            p.is_paid = status
            await session.commit()
            return True
        return False