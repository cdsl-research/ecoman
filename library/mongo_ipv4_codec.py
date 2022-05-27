import ipaddress

from bson.codec_options import TypeCodec
from bson.codec_options import TypeRegistry
from bson.codec_options import CodecOptions
from bson.int64 import Int64

class IPv4AddressCodec(TypeCodec):
    python_type = ipaddress.IPv4Address
    bson_type = Int64
    def transform_python(self, value):
        """Function that transforms a custom type value into a type
        that BSON can encode."""
        return Int64(value)

    def transform_bson(self, value):
        """Function that transforms a vanilla BSON type value into our
        custom type."""
        return ipaddress.IPv4Address(value)

ipv4_addr_codec = IPv4AddressCodec()
type_registry = TypeRegistry([ipv4_addr_codec])
codec_options = CodecOptions(type_registry=type_registry)
