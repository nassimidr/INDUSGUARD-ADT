from __future__ import annotations
from sqlalchemy import func,select
class Repository:
    def __init__(self,session,model):self.session=session;self.model=model
    def get(self,**filters):return self.session.scalar(select(self.model).filter_by(**filters))
    def list(self,page=1,page_size=25,order_by=None,**filters):
        statement=select(self.model).filter_by(**{k:v for k,v in filters.items() if v is not None});total=self.session.scalar(select(func.count()).select_from(statement.subquery())) or 0
        if order_by is not None:statement=statement.order_by(order_by)
        items=list(self.session.scalars(statement.offset((page-1)*page_size).limit(page_size)))
        return items,total
