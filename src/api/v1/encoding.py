import logging

from eth_utils import to_checksum_address
from marshmallow import Schema, fields, post_load
from marshmallow.exceptions import ValidationError
from typing import Any, Dict, List, NamedTuple, Optional, Mapping

from src.constants.constants import SUPPORTED_CHAINS
from src.typing import ChecksumAVAXAddress

log = logging.getLogger(__name__)

class EthereumAddressField(fields.Field):

    def _deserialize(
            self,
            value: str,
            attr: Optional[str],  # pylint: disable=unused-argument
            data: Optional[Mapping[str, Any]],  # pylint: disable=unused-argument
            **_kwargs: Any,
    ) -> ChecksumAVAXAddress:
        # Make sure that given value is an ethereum address
        try:
            address = to_checksum_address(value)
        except (ValueError, TypeError) as e:
            raise ValidationError(
                f'Given value {value} is not an ethereum address',
                field_name='address',
            ) from e

        return address

class ChainIdField(fields.Field):

    def _deserialize(
            self,
            value: str,
            attr: Optional[str],  # pylint: disable=unused-argument
            data: Optional[Mapping[str, Any]],  # pylint: disable=unused-argument
            **_kwargs: Any,
    ) -> str:
        # Make sure that given value is an suported chain id
        if str(value) in SUPPORTED_CHAINS:
            return value
        
        raise ValidationError(
            f'Given value {value} is not suported chain',
            field_name='chainid',
        )

class NFTsUserSchema(Schema):
    address = EthereumAddressField(required=True)
    chainID = ChainIdField(load_default="43114")

class NftSchema(Schema):
    address = EthereumAddressField(required=True)
    name = fields.String(required=True)
    symbol = fields.String(required=True)
    tokenId = fields.String(required=True)
    image = fields.String(required=True)

class PostVaultSchema(Schema):
    chainID = ChainIdField(required=True)
    name = fields.String(required=True)
    symbol = fields.String(required=True)
    supply = fields.String(required=True)
    price = fields.String(required=True)
    fee = fields.String(required=True)
    contract_address = EthereumAddressField(required=True)
    curator_address = EthereumAddressField(required=True)
    nfts = fields.List(fields.Nested(NftSchema), required=True)

class GetVaultsSchema(Schema):
    chainID = ChainIdField(required=True)
    page = fields.Integer(load_default=1)
    perpage = fields.Integer(load_default=15)
