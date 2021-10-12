import json

from typing import Any, Dict, List

from src.api.app import db

class Vault(db.Model):
    __tablename__ = 'vaults'
    name = db.Column(db.String(), nullable=False)
    symbol = db.Column(db.String(), nullable=False)
    supply = db.Column(db.String(), nullable=False)
    price = db.Column(db.String(), nullable=False)
    fee = db.Column(db.String(), nullable=False)
    contract_address = db.Column(db.String(), nullable=False,  primary_key=True)
    curator_address = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=False)
    verified = db.Column(db.Integer, nullable=False)
    nfts = db.Column(db.String(), nullable=False)
    chainId = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Vault {self.name}-{self.id}>'

    def deserialize(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "symbol": self.symbol,
            "supply": self.supply,
            "price": self.price,
            "fee": self.fee,
            "contract_address": self.contract_address,
            "curator_address": self.curator_address,
            "description": self.description,
            "verified": self.verified != 0,
            "nfts": json.loads(self.nfts),
        }

def db_insert(obj: object) -> None:
    db.session.add(obj)
    db.session.commit()

def db_query_filter(obj: object, expression: bool) -> List[object]:
    return db.session.query(obj).filter(expression).all()

def db_query_filter_pag(obj: object, expression: bool, page: int, per_page: int) -> List[object]:
    return db.session.query(obj).filter(expression).paginate(page, per_page, error_out=False)
