import logging

from eth_utils import to_checksum_address
from marshmallow import Schema, fields
from marshmallow.exceptions import ValidationError
from typing import Any, Optional, Mapping

from src.constants.constants import SUPORTED_CHAINS
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
        # Make sure that given value is an ethereum address
        if str(value) in SUPORTED_CHAINS:
            return value
        
        raise ValidationError(
            f'Given value {value} is not suported chain',
            field_name='chainid',
        )

class NFTsUserSchema(Schema):
    address = EthereumAddressField(load_default=None)
    chainID = ChainIdField(load_default="43114")