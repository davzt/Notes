from datetime import datetime
from typing import Any, Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import coalesce

from app.dependencies import get_async_session
from app.models import UserORM, NoteORM
from app.routers.exceptions import ErrorModel
from app.schemas import Note, NoteCreate, NoteUpdate

from app.auth import get_current_active_user, get_current_superuser


def get_note_router() -> APIRouter:
    router = APIRouter(
        tags=['notes']
    )

    # get_user_manager = fastapi_users.get_user_manager
    # authenticator = fastapi_users.authenticator
    #
    # get_current_active_user = authenticator.current_user(
    #     active=True, verified=requires_verification
    # )
    # get_current_superuser = authenticator.current_user(
    #     active=True, verified=requires_verification, superuser=True
    # )

    # async def get_user_or_404(
    #         id: Any,
    #         user_manager: BaseUserManager[models.UP, models.ID] = Depends(get_user_manager),
    # ) -> models.UP:
    #     try:
    #         parsed_id = user_manager.parse_id(id)
    #         return await user_manager.get(parsed_id)
    #     except (exceptions.UserNotExists, exceptions.InvalidID) as e:
    #         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from e

    @router.get(
        '/me/notes',
        response_model=Optional[list[Note]],
        dependencies=[Depends(get_current_active_user)],
        name="notes:get_notes",
        responses={
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Missing token or inactive user.",
            },
        }
    )
    async def get_notes(
            db: Annotated[AsyncSession, Depends(get_async_session)],
            user: Annotated[UserORM, Depends(get_current_active_user)],
            skip: int = 0,
            limit: int = 100
    ):
        query = select(NoteORM).join(UserORM.notes) \
            .where(UserORM.id == user.id).order_by(desc(coalesce(NoteORM.updated_at, NoteORM.created_at))) \
            .offset(skip).limit(limit)
        result = await db.execute(query)
        notes = []
        for row in result.all():
            notes.append(Note.from_orm(row[0]))

        return notes

    @router.get(
        '/me/notes/{note_id}',
        response_model=Optional[Note],
        dependencies=[Depends(get_current_active_user)],
        name="notes:get_note",
        responses={
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Missing token or inactive user.",
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "The note does not exist.",
            }
        }
    )
    async def get_note(
            db: Annotated[AsyncSession, Depends(get_async_session)],
            user: Annotated[UserORM, Depends(get_current_active_user)],
            note_id: int,
    ):
        query = select(NoteORM).join(UserORM.notes) \
            .where(and_(UserORM.id == user.id, NoteORM.note_id == note_id))
        result = await db.execute(query)
        note_db = result.scalar_one_or_none()
        if note_db is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="The note does not exist.")
        return Note.from_orm(note_db)

    @router.patch(
        "/me/notes/{note_id}",
        response_model=Note,
        dependencies=[Depends(get_current_active_user)],
        name="notes:update_note",
        responses={
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Missing token or inactive user.",
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "The note does not exist.",
            },
            status.HTTP_400_BAD_REQUEST: {
                "model": ErrorModel,
                "content": {
                    "application/json": {
                        "examples": {
                            "UPDATE_NOTE_TITLE_ALREADY_EXISTS": {
                                "summary": "Note with that title already exists",
                                "value": {
                                    "detail": "UPDATE_NOTE_TITLE_ALREADY_EXISTS"
                                },
                            },
                            "UPDATE_NOTE_INVALID_TIME_LIMIT": {
                                "summary": "Incorrect time limit value.",
                                "value": {
                                    "detail": {
                                        "code": "UPDATE_NOTE_INVALID_TIME_LIMIT",
                                        "reason": "Time limit should be"
                                                  "later than now",
                                    }
                                },
                            },
                        }
                    }
                },
            }
        }
    )
    async def update_note(
            note_id: int,
            note_update: NoteUpdate,
            db: Annotated[AsyncSession, Depends(get_async_session)],
            user: Annotated[UserORM, Depends(get_current_active_user)],
    ):
        query = select(NoteORM).join(UserORM.notes) \
            .where(and_(UserORM.id == user.id, NoteORM.note_id == note_id))
        result = await db.execute(query)
        note_db = result.scalar_one_or_none()
        if note_db is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="The note does not exist.")
        update_dict = note_update.dict(exclude_unset=True)
        update_dict['updated_at'] = datetime.utcnow()
        if 'title' in update_dict:
            query = select(NoteORM.title).join(UserORM.notes) \
                .where(and_(UserORM.id == user.id, NoteORM.title == update_dict['title']))
            result = await db.execute(query)
            if result.scalar_one_or_none() is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail='An article with this title already exists')

        if not update_dict.get('is_time_limited', True):
            update_dict['time_limit'] = None
        if 'time_limit' in update_dict and update_dict.get('is_time_limited', note_db.is_time_limited):
            if update_dict['time_limit'].strftime('%Y-%m-%dT%H:%M') <= datetime.utcnow().strftime('%Y-%m-%dT%H:%M'):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail='Incorrect time limit value.')
        for key, value in update_dict.items():
            setattr(note_db, key, value)
        db.add(note_db)
        await db.commit()
        await db.refresh(note_db)
        return Note.from_orm(note_db)

    @router.put(
        '/me/notes',
        response_model=Note,
        dependencies=[Depends(get_current_active_user)],
        name="notes:create_note",
        responses={
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Missing token or inactive user.",
            },
            status.HTTP_400_BAD_REQUEST: {
                "model": ErrorModel,
                "content": {
                    "application/json": {
                        "examples": {
                            "CREATE_NOTE_TITLE_ALREADY_EXISTS": {
                                "summary": "Note with that title already exists",
                                "value": {
                                    "detail": "CREATE_NOTE_TITLE_ALREADY_EXISTS"
                                },
                            },
                            "CREATE_NOTE_INVALID_TIME_LIMIT": {
                                "summary": "Incorrect time limit value.",
                                "value": {
                                    "detail": {
                                        "code": "CREATE_NOTE_INVALID_TIME_LIMIT",
                                        "reason": "Time limit should be"
                                                  "later than now",
                                    }
                                },
                            },
                        }
                    }
                },
            }
        }
    )
    async def create_note(
            db: Annotated[AsyncSession, Depends(get_async_session)],
            user: Annotated[UserORM, Depends(get_current_active_user)],
            note_create: NoteCreate
    ):

        create_dict = note_create.dict()
        if not create_dict['is_time_limited']:
            create_dict['time_limit'] = None
        elif create_dict['time_limit'].strftime('%Y-%m-%dT%H:%M') <= datetime.utcnow().strftime('%Y-%m-%dT%H:%M'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='Incorrect time limit value.')
        query = select(NoteORM.title).join(UserORM.notes) \
            .where(and_(UserORM.id == user.id, NoteORM.title == create_dict['title']))
        result = await db.execute(query)
        if result.scalar_one_or_none() is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='An article with this title already exists')
        note = NoteORM(**create_dict, user_id=user.id)
        db.add(note)
        await db.commit()
        return note

    @router.delete(
        '/me/notes/{note_id}',
        response_class=Response,
        dependencies=[Depends(get_current_active_user)],
        name="notes:delete_note",
        responses={
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Missing token or inactive user.",
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "The note does not exist.",
            }
        }
    )
    async def delete_note(
            db: Annotated[AsyncSession, Depends(get_async_session)],
            user: Annotated[UserORM, Depends(get_current_active_user)],
            note_id: int,
    ):
        note_db = None
        for note in user.notes:
            if note.note_id == note_id:
                note_db = note
        if note_db is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="The note does not exist.")
        await db.delete(note_db)
        await db.commit()
        return None

    @router.delete(
        '/{user_id}/notes/{note_id}',
        response_class=Response,
        dependencies=[Depends(get_current_superuser)],
        name="notes:delete_note_by_user_id",
        responses={
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Missing token or inactive user.",
            },
            status.HTTP_404_NOT_FOUND: {
                "model": ErrorModel,
                "content": {
                    "application/json": {
                        "examples": {
                            "DELETE_NOTE_USER_DOESNT_EXIST": {
                                "summary": "The user does not exist.",
                                "value": {
                                    "detail": "DELETE_NOTE_USER_DOESNT_EXIST"
                                },
                            },
                            "DELETE_NOTE_NOTE_DOESNT_EXIST": {
                                "summary": "The note does not exist.",
                                "value": {
                                    "detail": "DELETE_NOTE_NOTE_DOESNT_EXIST"
                                },
                            },
                        }
                    }
                },
            }
        }
    )
    async def delete_note_by_user_id(
            db: Annotated[AsyncSession, Depends(get_async_session)],
            note_id: int,
            user_id: UUID,
    ):
        query = select(UserORM).where(UserORM.id == user_id)
        result = await db.execute(query)
        user_db = result.scalar_one_or_none()
        if user_db is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="The user does not exist.")
        note_db = None
        for note in user_db.notes:
            if note.note_id == note_id:
                note_db = note
        if note_db is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="The note does not exist.")
        await db.delete(note_db)
        await db.commit()
        return None

    @router.get(
        '/{user_id}/notes/{note_id}',
        response_model=Note,
        dependencies=[Depends(get_current_superuser)],
        name="notes:get_note_by_user_id",
        responses={
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Missing token or inactive user.",
            },
            status.HTTP_404_NOT_FOUND: {
                "model": ErrorModel,
                "content": {
                    "application/json": {
                        "examples": {
                            "DELETE_NOTE_USER_DOESNT_EXIST": {
                                "summary": "The user does not exist.",
                                "value": {
                                    "detail": "DELETE_NOTE_USER_DOESNT_EXIST"
                                },
                            },
                            "DELETE_NOTE_NOTE_DOESNT_EXIST": {
                                "summary": "The note does not exist.",
                                "value": {
                                    "detail": "DELETE_NOTE_NOTE_DOESNT_EXIST"
                                },
                            },
                        }
                    }
                },
            }
        }
    )
    async def get_note_by_user_id(
            db: Annotated[AsyncSession, Depends(get_async_session)],
            note_id: int,
            user_id: UUID,
    ):
        query = select(UserORM).where(UserORM.id == user_id)
        result = await db.execute(query)
        user_db = result.scalar_one_or_none()
        if user_db is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="The user does not exist.")
        note_db = None
        for note in user_db.notes:
            if note.note_id == note_id:
                note_db = note
        if note_db is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="The note does not exist.")
        return Note.from_orm(note_db)

    @router.get(
        '/{user_id}/notes',
        response_model=Optional[list[Note]],
        dependencies=[Depends(get_current_superuser)],
        name="notes:get_notes_by_user_id",
        responses={
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Missing token or inactive user.",
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "The user does not exist.",
            }
        }
    )
    async def get_notes_by_user_id(
            db: Annotated[AsyncSession, Depends(get_async_session)],
            user_id: UUID,
            skip: int = 0,
            limit: int = 100,
    ):
        query = select(UserORM).where(UserORM.id == user_id)
        result = await db.execute(query)
        user_db = result.scalar_one_or_none()
        if user_db is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="The user does not exist.")
        query = select(NoteORM).join(UserORM.notes) \
            .where(UserORM.id == user_id).order_by(desc(coalesce(NoteORM.updated_at, NoteORM.created_at)))\
            .offset(skip).limit(limit)
        result = await db.execute(query)
        notes = []
        for row in result.all():
            notes.append(Note.from_orm(row[0]))
        return notes

    @router.patch(
        "/{user_id}/notes/{note_id}",
        response_model=Note,
        dependencies=[Depends(get_current_superuser)],
        name="notes:update_note_by_user_id",
        responses={
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Missing token or inactive user.",
            },
            status.HTTP_404_NOT_FOUND: {
                "model": ErrorModel,
                "content": {
                    "application/json": {
                        "examples": {
                            "UPDATE_NOTE_USER_DOESNT_EXIST": {
                                "summary": "The user does not exist.",
                                "value": {
                                    "detail": "UPDATE_NOTE_USER_DOESNT_EXIST"
                                },
                            },
                            "UPDATE_NOTE_NOTE_DOESNT_EXIST": {
                                "summary": "The note does not exist.",
                                "value": {
                                    "detail": "UPDATE_NOTE_NOTE_DOESNT_EXIST"
                                },
                            },
                        }
                    }
                },
            },
            status.HTTP_400_BAD_REQUEST: {
                "model": ErrorModel,
                "content": {
                    "application/json": {
                        "examples": {
                            "UPDATE_NOTE_TITLE_ALREADY_EXISTS": {
                                "summary": "Note with that title already exists",
                                "value": {
                                    "detail": "UPDATE_NOTE_TITLE_ALREADY_EXISTS"
                                },
                            },
                            "UPDATE_NOTE_INVALID_TIME_LIMIT": {
                                "summary": "Incorrect time limit value.",
                                "value": {
                                    "detail": {
                                        "code": "UPDATE_NOTE_INVALID_TIME_LIMIT",
                                        "reason": "Time limit should be"
                                                  "later than now",
                                    }
                                },
                            },
                        }
                    }
                },
            }
        }
    )
    async def update_note_by_user_id(
            user_id: UUID,
            note_id: int,
            note_update: NoteUpdate,
            db: Annotated[AsyncSession, Depends(get_async_session)],
    ):
        query = select(UserORM).where(UserORM.id == user_id)
        result = await db.execute(query)
        user_db = result.scalar_one_or_none()
        if user_db is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="The user does not exist.")
        note_db = None
        for note in user_db.notes:
            if note.note_id == note_id:
                note_db = note
        if note_db is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="The note does not exist.")
        update_dict = note_update.dict(exclude_unset=True)
        update_dict['updated_at'] = datetime.utcnow()
        if 'title' in update_dict:
            query = select(NoteORM.title).join(UserORM.notes) \
                .where(and_(UserORM.id == user_id, NoteORM.title == update_dict['title']))
            result = await db.execute(query)
            if result.scalar_one_or_none() is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail='An article with this title already exists')

        if not update_dict.get('is_time_limited', True):
            update_dict['time_limit'] = None
        if 'time_limit' in update_dict and update_dict.get('is_time_limited', note_db.is_time_limited):
            if update_dict['time_limit'].strftime('%Y-%m-%dT%H:%M') <= datetime.utcnow().strftime('%Y-%m-%dT%H:%M'):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail='Incorrect time limit value.')
        for key, value in update_dict.items():
            setattr(note_db, key, value)
        db.add(note_db)
        await db.commit()
        await db.refresh(note_db)
        return Note.from_orm(note_db)

    @router.put(
        '/{user_id}/notes',
        response_model=Note,
        dependencies=[Depends(get_current_superuser)],
        name="notes:create_note_by_user_id",
        responses={
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Missing token or inactive user.",
            },
            status.HTTP_400_BAD_REQUEST: {
                "model": ErrorModel,
                "content": {
                    "application/json": {
                        "examples": {
                            "CREATE_NOTE_TITLE_ALREADY_EXISTS": {
                                "summary": "Note with that title already exists",
                                "value": {
                                    "detail": "CREATE_NOTE_TITLE_ALREADY_EXISTS"
                                },
                            },
                            "CREATE_NOTE_INVALID_TIME_LIMIT": {
                                "summary": "Incorrect time limit value.",
                                "value": {
                                    "detail": {
                                        "code": "CREATE_NOTE_INVALID_TIME_LIMIT",
                                        "reason": "Time limit should be"
                                                  "later than now",
                                    }
                                },
                            },
                        }
                    }
                },
            }
        }
    )
    async def create_note_by_user_id(
            user_id: UUID,
            db: Annotated[AsyncSession, Depends(get_async_session)],
            note_create: NoteCreate
    ):
        query = select(UserORM).where(UserORM.id == user_id)
        result = await db.execute(query)
        user_db = result.scalar_one_or_none()
        if user_db is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="The user does not exist.")
        create_dict = note_create.dict()
        if not create_dict['is_time_limited']:
            create_dict['time_limit'] = None
        elif create_dict['time_limit'].strftime('%Y-%m-%dT%H:%M') <= datetime.utcnow().strftime('%Y-%m-%dT%H:%M'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='Incorrect time limit value.')
        query = select(NoteORM.title).join(UserORM.notes) \
            .where(and_(UserORM.id == user_id, NoteORM.title == create_dict['title']))
        result = await db.execute(query)
        if result.scalar_one_or_none() is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='An article with this title already exists')
        note = NoteORM(**create_dict, user_id=user_id)
        db.add(note)
        await db.commit()
        return note

    return router
