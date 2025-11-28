from typing import List, Optional, Type
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.chatbot import Chatbot
from app.schemas.chatbot import ChatbotCreate, ChatbotUpdate


class ChatbotRepository:
    def __init__(self, db: Session):
        self.db = db
        self.model = Chatbot

    def get(self, id: UUID) -> Optional[Chatbot]:
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_multi(self, skip: int = 0, limit: int = 100) -> List[Chatbot]:
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, obj_in: ChatbotCreate) -> Chatbot:
        db_obj = self.model(
            name=obj_in.name,
            model_name=obj_in.model_name,
            llm_config=obj_in.llm_config,
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: Chatbot, obj_in: ChatbotUpdate) -> Chatbot:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: UUID) -> Optional[Chatbot]:
        obj = self.db.query(self.model).get(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
        return obj
